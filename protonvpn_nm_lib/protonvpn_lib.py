from .logger import logger
from . import exceptions
from .enums import KillswitchStatusEnum, ConnectionTypeEnum
from .services.certificate_manager import CertificateManager
from .services.connection_manager import ConnectionManager
from .services.ipv6_leak_protection_manager import IPv6LeakProtectionManager
from .services.killswitch_manager import KillSwitchManager
from .services.reconnector_manager import ReconnectorManager
from .services.server_manager import ServerManager
from .services.user_configuration_manager import UserConfigurationManager
from .services.user_manager import UserManager
from .connect import Connect
from .disconnect import Disconnect
from .login import Login
from .logout import Logout
from .reconnect import Reconnect
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from .constants import VIRTUAL_DEVICE_NAME


class ProtonVPNNMLib(
    Connect, Disconnect,
    Login, Logout, Reconnect
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
        DBusGMainLoop(set_as_default=True)
        self.dbus_loop = GLib.MainLoop()

    def get_existing_session(
        self, return_bool=False, skip_raise_for_no_session=False
    ):
        """Proxymethod to get user session."""
        logger.info("Attempting to get existing session")
        try:
            self.session = self.user_manager.load_session()
        except exceptions.JSONDataEmptyError:
            raise Exception(
                "The stored session might be corrupted. "
                + "Please, try to login again."
            )
        except (
            exceptions.JSONDataError,
            exceptions.JSONDataNoneError
        ):
            message = "There is no stored session. Please, login first."
            if not skip_raise_for_no_session:
                raise Exception(message)
            return message
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

        if return_bool:
            return True if self.session else False

    def refresh_servers(self, session):
        if self.user_conf_manager.killswitch != KillswitchStatusEnum.HARD.value:
            try:
                session.cache_servers()
            except (exceptions.ProtonVPNException, Exception) as e:
                raise Exception(e)

    def remove_existing_connection(self):
        try:
            self.connection_manager.remove_connection(
                self.user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                self.reconector_manager
            )
        except exceptions.ConnectionNotFound:
            pass

    def check_connectivity(self):
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

    def setup_dbus_vpn_monitor(self, dbus_response):
        self.vpn_monitor_connection_start.setup_monitor(
            VIRTUAL_DEVICE_NAME, self.dbus_loop,
            self.ks_manager, self.user_conf_manager,
            self.connection_manager, self.reconector_manager,
            self.session, dbus_response
        )

    def start_dbus_vpn_monitor(self):
        self.vpn_monitor_connection_start.start_monitor()
        self.dbus_loop.run()
