import datetime
import time

import dbus

from . import exceptions
from .constants import SUPPORTED_FEATURES
from .enums import (ConnectionMetadataEnum, ConnectionTypeEnum, FeatureEnum,
                    KillswitchStatusEnum, MetadataEnum,
                    NetworkManagerConnectionTypeEnum, ServerInfoEnum)
from .lib.connect import Connect
from .lib.disconnect import Disconnect
from .lib.login import Login
from .lib.logout import Logout
from .lib.reconnect import Reconnect
from .lib.status import Status
from .lib.user_settings import UserSettings
from .logger import logger
from .services.certificate_manager import CertificateManager
from .services.connection_manager import ConnectionManager
from .services.ipv6_leak_protection_manager import IPv6LeakProtectionManager
from .services.killswitch_manager import KillSwitchManager
from .services.proton_session_wrapper import ProtonSessionWrapper
from .services.reconnector_manager import ReconnectorManager
from .services.server_manager import ServerManager
from .services.user_configuration_manager import UserConfigurationManager
from .services.user_manager import UserManager


class ProtonVPNNMLib(
    Connect, Disconnect,
    Login, Logout, Reconnect,
    UserSettings, Status
):
    def __init__(self, vpn_monitor_connection_start):
        self.vpn_monitor_connection_start = vpn_monitor_connection_start
        self.reconector_manager = ReconnectorManager()
        self.user_conf_manager = UserConfigurationManager()
        self.ks_manager = KillSwitchManager(self.user_conf_manager)
        self.connection_manager = ConnectionManager()
        self.user_manager = UserManager(self.user_conf_manager)
        self.server_manager = ServerManager(
            CertificateManager(), self.user_manager
        )
        self.ipv6_lp_manager = IPv6LeakProtectionManager()
        self.protocol = None
        self.connect_type = None
        self.connect_type_extra_arg = None
        self.CONNECT_TYPE_DICT = {
            ConnectionTypeEnum.SERVERNAME: self.server_manager.get_config_for_specific_server, # noqa
            ConnectionTypeEnum.FASTEST: self.server_manager.get_config_for_fastest_server, # noqa
            ConnectionTypeEnum.RANDOM: self.server_manager.get_config_for_random_server, # noqa
            ConnectionTypeEnum.COUNTRY: self.server_manager.get_config_for_fastest_server_in_country, # noqa
            ConnectionTypeEnum.SECURE_CORE: self.server_manager.get_config_for_fastest_server_with_specific_feature, # noqa
            ConnectionTypeEnum.PEER2PEER: self.server_manager.get_config_for_fastest_server_with_specific_feature, # noqa
            ConnectionTypeEnum.TOR: self.server_manager.get_config_for_fastest_server_with_specific_feature # noqa
        }

    def _get_connection_metadata(
        self,
        network_manager_connection_type=NetworkManagerConnectionTypeEnum.ACTIVE
    ):
        connection_exists = self.connection_manager.get_protonvpn_connection(
            network_manager_connection_type
        )

        if not connection_exists[0]:
            return False

        return self.connection_manager.get_connection_metadata(
            MetadataEnum.CONNECTION
        )

    def _get_user_tier(self):
        try:
            return self.user_manager.tier
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _extraxt_country_name(self, exit_country):
        return self.server_manager.extract_country_name(exit_country)

    def _filter_servers(self, server_list):
        try:
            return self.server_manager.filter_servers(
                server_list
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _get_server_list(self):
        try:
            return self.server_manager.extract_server_list()
        except (exceptions.ProtonVPNExceptionm, Exception) as e:
            raise Exception(e)

    def _generate_country_servername_dict(self, server_list):
        """Generate country:servername

        Args:
            servers (list): contains server information about each country
        Returns:
            dict: country_code: [servername]
                ie {PT: [PT#5, PT#8]}
        """
        countries = {}
        for server in server_list:
            country = self._extraxt_country_name(server["ExitCountry"]) # noqa
            if country not in countries.keys():
                countries[country] = []
            countries[country].append(server["Name"])

        return countries

    def _get_protonvpn_connection(self, network_manager_connection_type):
        try:
            return self.connection_manager.get_protonvpn_connection(
                network_manager_connection_type
            )
        except (dbus.DBusException, Exception) as e:
            logger.exception(e)
            return False

    def _remove_existing_connection(self):
        try:
            self.connection_manager.remove_connection(
                self.user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                self.reconector_manager
            )
        except exceptions.ConnectionNotFound:
            pass

    def _validate_session(self, session=None):
        """Validates session.

        Args:
            session (proton.api.Session): current user session
        """
        logger.info("Validating session")
        if session is None:
            session = self.session

        if not isinstance(session, ProtonSessionWrapper):
            err_msg = "Incorrect object type, "\
                "{} is expected "\
                "but got {} instead".format(
                    ProtonSessionWrapper, session
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise TypeError(err_msg)

    def _check_connectivity(self):
        # check if there is internet connectivity
        try:
            self.connection_manager.is_internet_connection_available(
                self.user_conf_manager.killswitch
            )
        except exceptions.InternetConnectionError as e:
            raise Exception("\n{}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception(e)

        # check if API is reachable
        try:
            self.connection_manager.is_api_reacheable(
                self.user_conf_manager.killswitch
            )
        except exceptions.APITimeoutError as e:
            raise Exception(
                "{}".format(e)
            )
        except exceptions.UnreacheableAPIError as e:
            raise Exception(
                "{}".format(e)
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception("{}".format(e))

    def _refresh_servers(self):
        self._set_self_session()
        if self.user_conf_manager.killswitch != KillswitchStatusEnum.HARD:
            try:
                self.session.cache_servers()
            except (exceptions.ProtonVPNException, Exception) as e:
                raise Exception(e)

    def _set_self_session(self):
        self.__get_existing_session()

    def _get_session(self):
        try:
            return self.__get_existing_session(return_session=True)
        except exceptions.StoredSessionNotFound as e:
            raise exceptions.StoredSessionNotFound(e)
        except exceptions.IllegalSessionData as e:
            raise exceptions.IllegalSessionData(e)
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _check_session_exists(self):
        try:
            return self.__get_existing_session(return_bool=True)
        except (exceptions.ProtonVPNException, Exception):
            return False

    def __get_existing_session(
        self, return_bool=False, return_session=False
    ):
        """Private method.

        Gets the session. Default behaviour is
        to update instance session, but it can also return
        the session if return_session=True. It can also return bool
        if return_bool=True, returning True if session exists,
        False otherwise.

        Args:
            return_bool (bool):
                (optional) should be true if
                boolean is value requested.
            return_session (bool):
                (optional) should be true if
                session instance is to be returned.
        """
        logger.info("Attempting to get existing session")
        session = None
        try:
            session = self.user_manager.load_session()
        except exceptions.JSONDataEmptyError:
            raise exceptions.IllegalSessionData(
                "The stored session might be corrupted. "
                + "Please, try to login again."
            )
        except (
            exceptions.JSONDataError,
            exceptions.JSONDataNoneError
        ):
            raise exceptions.StoredSessionNotFound(
                "There is no stored session. Please, login first."
            )
        except exceptions.AccessKeyringError as e:
            logger.exception(e)
            raise Exception(
                "Unable to load session. Could not access keyring."
            )
        except exceptions.KeyringError as e:
            logger.exception(e)
            raise Exception("Unknown keyring error occured: {}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}.".format(e))

        logger.info("Session found.")

        if return_bool and not return_session:
            return True if session else False
        elif not return_bool and return_session:
            return session
        else:
            self.session = session

    def _get_server_information(self, servername=None):
        if not servername:
            conn_status = self.connection_manager.display_connection_status()
            try:
                servername = conn_status[ConnectionMetadataEnum.SERVER.value]
            except KeyError:
                servername = None

        return self.__extract_server_info(servername)

    def __extract_server_info(self, servername):
        """Extract server information.

        Args:
            servername (string): servername [PT#1]

        Returns:
            dict:
                Keys: ServerInfoEnum
        """
        self._refresh_servers()
        servers = self.server_manager.extract_server_list()
        try:
            country_code = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.COUNTRY.value, servers
            )
            country = self.server_manager.extract_country_name(country_code)

            load = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.LOAD.value, servers
            )
            features = [
                self.server_manager.extract_server_value(
                    servername, ServerInfoEnum.FEATURES.value, servers
                )
            ]

            city = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.CITY.value, servers
            )

            region = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.REGION.value, servers
            )

            location = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.LOCATION.value, servers
            )

            entry_country = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.ENTRY_COUNTRY.value, servers
            )
            entry_country = self.server_manager.extract_country_name(
                entry_country
            )

            tier = [
                self.server_manager.extract_server_value(
                    servername, ServerInfoEnum.TIER.value, servers
                )
            ].pop()
        except IndexError as e:
            logger.exception("[!] IndexError: {}".format(e))
            raise IndexError(
                "\nThe server you have connected to is not available. "
                "If you are currently connected to the server, "
                "you will be soon disconnected. "
                "Please connect to another server."
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception("[!] Unknown error: {}".format(e))
            raise Exception("\nUnknown error: {}".format(e))

        feature_list = []
        for feature in features:
            feature = FeatureEnum(feature)
            if feature in SUPPORTED_FEATURES:
                feature_list.append(feature)

        return {
            ServerInfoEnum.SERVERNAME: servername,
            ServerInfoEnum.COUNTRY: country,
            ServerInfoEnum.CITY: city,
            ServerInfoEnum.LOAD: load,
            ServerInfoEnum.TIER: tier,
            ServerInfoEnum.FEATURES: feature_list,
            ServerInfoEnum.LOCATION: location,
            ServerInfoEnum.ENTRY_COUNTRY: entry_country,
            ServerInfoEnum.REGION: region,
        }

    def _convert_time_from_epoch(self, seconds_since_epoch):
        """Convert time from epoch to 24h.

        Args:
           time_in_epoch (string): time in seconds since epoch

        Returns:
            string: time in 24h format, since last connection was made
        """
        connection_time = (
            time.time()
            - int(seconds_since_epoch)
        )
        return str(
            datetime.timedelta(
                seconds=connection_time
            )
        ).split(".")[0]
