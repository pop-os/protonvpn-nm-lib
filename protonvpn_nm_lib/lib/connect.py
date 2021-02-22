from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from .. import exceptions
from ..constants import FLAT_SUPPORTED_PROTOCOLS, VIRTUAL_DEVICE_NAME
from ..enums import (ConnectionTypeEnum, DbusMonitorResponseEnum,
                     NetworkManagerConnectionTypeEnum, ProtocolEnum)
from ..logger import logger
from ..core.certificate_manager import CertificateManager


class ProtonVPNConnect():
    """Connect Class.
    Use it to setup and connect to VPN.

    Exposes methods:
        _setup_connection(
            connection_type: ConnectionTypeEnum,
            connection_type_extra_arg=None: String,
            protocol=None: String
        )
        _connect()

    Description:
    _setup_connection()
        Prepares the connection to be started, by adding it to NetworkManager.
        It collects are necessary information, including
        openvpn username and password.
        This should always be run before _connect().

    _connect()
        Starts the VPN connection. To follow-up the state of the VPN,
        a vpn monitor state is started, which is passed a list which will
        contain the response of the vpn connection state. As soon as the loop
        is quit, the _connect() will return a response of the status
        of the VPN in dict form.
    """

    def __init__(
        self, connection, session, server, server_list, disconnect,
        country, connection_manager, server_manager,
        user_manager, user_conf_manager,
        ks_manager, vpn_monitor_connection_start,
        ipv6_lp_manager, reconector_manager
    ):
        # library
        self.connection = connection
        self.session = session
        self.server = server
        self.server_list = server_list
        self.disconnect = disconnect
        self.country = country

        # core
        self.__connection_manager = connection_manager
        self.__server_manager = server_manager
        self.__user_manager = user_manager
        self.__user_conf_manager = user_conf_manager
        self.__ks_manager = ks_manager
        self.__vpn_monitor_connection_start = vpn_monitor_connection_start
        self.__ipv6_lp_manager = ipv6_lp_manager
        self.__reconector_manager = reconector_manager

        self.__user_session = None
        self.__connect_type = None
        self.__connect_type_extra_arg = None
        self.__connect_type_DICT = {
            ConnectionTypeEnum.SERVERNAME: self.__server_manager.get_config_for_specific_server, # noqa
            ConnectionTypeEnum.FASTEST: self.__server_manager.get_config_for_fastest_server, # noqa
            ConnectionTypeEnum.RANDOM: self.__server_manager.get_config_for_random_server, # noqa
            ConnectionTypeEnum.COUNTRY: self.__server_manager.get_config_for_fastest_server_in_country, # noqa
            ConnectionTypeEnum.SECURE_CORE: self.__server_manager.get_config_for_fastest_server_with_specific_feature, # noqa
            ConnectionTypeEnum.PEER2PEER: self.__server_manager.get_config_for_fastest_server_with_specific_feature, # noqa
            ConnectionTypeEnum.TOR: self.__server_manager.get_config_for_fastest_server_with_specific_feature # noqa
        }

    def _connect(self):
        """Public method.

        Connects to VPN with previously
        setup configurations.

        It is recommended to either run
        connect._setup_connection() or reconnect._setup_reconnect()
        before calling this method.

        Returns:
            string: response from dbus monitor
        """
        dbus_response = {DbusMonitorResponseEnum.RESPONSE: ""}
        self.__connection_manager.start_connection()
        self.__setup_dbus_vpn_monitor(dbus_response)
        self.__start_dbus_vpn_monitor()
        return dbus_response.get(DbusMonitorResponseEnum.RESPONSE)

    def _setup_connection(
        self,
        connection_type,
        connection_type_extra_arg=None,
        protocol=None
    ):
        """Public method.

        Setup and configure VPN connection prior
        calling connect._connect().

        Args:
            connection_type (ConnectionTypeEnum):
                selected connection type
            connection_type_extra_arg (string):
                (optional) should be used only when
                connecting directly to a specific server
                with ConnectionTypeEnum.SERVERNAME or when
                connecting to a specific country with
                ConnectionTypeEnum.COUNTRY.
            optional protocol (ProtocolEnum): ProtocolEnum.TPC
                (optional) if None, then protocol will be fetched
                from user configurations.

        Returns:
            dict: contains connection information to be displayed for the user.
        """
        servername = None
        if connection_type == ConnectionTypeEnum.SERVERNAME:
            servername = connection_type_extra_arg
        elif (
            connection_type == ConnectionTypeEnum.COUNTRY
            and not self.country._check_country_exists(
                connection_type_extra_arg
            )
        ):
            raise exceptions.InvalidCountryCode(
                "The provided country code \"{}\" is invalid.".format(
                    connection_type_extra_arg
                )
            )

        self.connection_type = connection_type
        self.connection_type_extra_arg = connection_type_extra_arg

        if servername: self.server._ensure_servername_is_valid(servername) # noqa

        self.__user_session = self.session._get_session()
        self.session._ensure_session_is_valid(self.__user_session)

        if not self._is_protocol_valid(protocol):
            protocol = ProtocolEnum(
                self.__user_conf_manager.default_protocol
            )
        else:
            protocol = ProtocolEnum(protocol)

        logger.info("Setup protocol: {}".format(protocol))

        self.__server_manager.killswitch_status = self.__user_conf_manager.killswitch # noqa
        logger.info("Setup killswitch user setting")

        self.session._ensure_connectivity()
        logger.info("Checked for internet and api connectivity")

        try:
            self.disconnect._disconnect()
        except exceptions.ConnectionNotFound:
            pass
        logger.info("Removed any possible existing connection")

        openvpn_username, openvpn_password = self.__get_ovpn_credentials()
        logger.info("OpenVPN credentials collected")

        connection_info = self.__add_connection(
            openvpn_username, openvpn_password, protocol
        )

        logger.info("Returning connection information")
        return connection_info

    def _is_protocol_valid(self, protocol):
        """Check if provided protocol is a valid protocol.

        Args:
            protocol (ProtocolEnum)

        Returns:
            bool
        """
        logger.info("Checking if protocol is valid")
        try:
            protocol = ProtocolEnum(protocol)
        except (TypeError, ValueError):
            return False

        if protocol in FLAT_SUPPORTED_PROTOCOLS:
            return True

        return False

    def __add_connection(self, openvpn_username, openvpn_password, protocol):
        """Add ProtonVPN connection.

        Args:
            openvpn_username (string): OpenVPN username
            openvpn_password (string): OpenVPN password
            protocol (ProtocolEnum)

        Returns:
            dict: connection metadata
        """
        self.server_list._refresh_servers()
        (
            servername, domain,
            server_feature,
            filtered_servers, servers
        ) = self.__collect_server_information()

        logger.info("Generated connection configuration.")

        (
            certificate_fp,
            matching_domain,
            entry_ip,
            server_label
        ) = self.__server_manager.generate_server_certificate(
            servername, domain, server_feature,
            protocol, servers, filtered_servers
        )
        logger.info("Generated certificate.")

        if server_label is not None:
            openvpn_username = openvpn_username + "+b:" + server_label
            logger.info("Appended server label.")

        self.__add_vpn_connection_to_nm(
            certificate_fp, openvpn_username, openvpn_password,
            matching_domain, entry_ip
        )
        logger.info("Added VPN connection to NetworkManager.")

        connection_info = self.connection._get_connection_metadata(
            NetworkManagerConnectionTypeEnum.ALL
        )

        return connection_info

    def __add_vpn_connection_to_nm(
        self, certificate_filename, openvpn_username,
        openvpn_password, domain, entry_ip
    ):
        """Proxymethod to add connection to NetworkManager.

        Args:
            certificate_filename (string): path to certificate
            openvpn_username (string): OpenVPN username
            openvpn_password (string): OpenVPN password
            domain (string): selected subserver domain
            entry_ip (string): selected subserver entry_ip
        """
        try:
            self.__connection_manager.add_connection(
                certificate_filename, openvpn_username, openvpn_password,
                CertificateManager.delete_cached_certificate, domain,
                self.__user_conf_manager, self.__ks_manager,
                self.__ipv6_lp_manager, entry_ip
            )
        except exceptions.ImportConnectionError as e:
            logger.exception("ImportConnectionError: {}".format(e))
            raise Exception("An error occured upon importing connection: ", e)
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error: {}".format(e))

    def __get_ovpn_credentials(self, retry=False):
        """Proxymethod to get OVPN credentials.

        Returns:
            tuple: openvpnvpn_username, openvpn_password
        """
        logger.info("Getting openvpn credentials")

        try:
            if retry:
                self.__user_manager.cache_user_data()
            return self.__user_manager.get_stored_vpn_credentials( # noqa
                self.__user_session
            )
        except exceptions.JSONDataEmptyError:
            raise Exception(
                "The stored session might be corrupted. "
                + "Please, try to login again."
            )
        except (
            exceptions.JSONDataError,
            exceptions.JSONDataNoneError
        ) as e:
            if retry:
                raise Exception(e)
            return self.__get_ovpn_credentials(retry=True)
        except exceptions.APITimeoutError as e:
            logger.exception(
                "APITimeoutError: {}".format(e)
            )
            raise Exception("Connection timeout, unable to reach API.")
        except exceptions.API10013Error:
            raise Exception(
                "Current session is invalid, "
                "please logout and login again."
            )
        except exceptions.ProtonSessionWrapperError as e:
            logger.exception(
                "Unknown ProtonSessionWrapperError: {}".format(e)
            )
            raise Exception("Unknown API error occured: {}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}.".format(e))

    def __collect_server_information(self):
        """Proxymethod to collect server information
        for specified connection_type.

        Returns:
            tuple: (
                servername, server_domain, server_feature,
                filtered_server_list, server_list
            )
        """
        logger.info(
            "Connect type: {} - {}".format(
                self.connection_type,
                type(self.connection_type),
            )
        )
        logger.info(
            "Connect type extra arg: {} - {}".format(
                self.connection_type_extra_arg,
                type(self.connection_type_extra_arg),
            )
        )
        try:
            return self.__connect_type_DICT[self.connection_type](
                self.connection_type_extra_arg
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.exception("Error: {}".format(e))
            raise Exception("Error: {}".format(e))
        except exceptions.EmptyServerListError as e:
            logger.exception("Error: {}".format(e))
            raise Exception(
                "{} This could mean that the ".format(e)
                + "server(s) are under maintenance or "
                + "inaccessible with your plan."
            )
        except exceptions.IllegalServername as e:
            raise Exception("IllegalServername: {}".format(e))
        except exceptions.CacheLogicalServersError as e:
            raise Exception("CacheLogicalServersError: {}".format(e))
        except exceptions.MissingCacheError as e:
            raise Exception("MissingCacheError: {}".format(e))
        except exceptions.API403Error as e:
            raise Exception("API403Error: {}".format(e.error))
        except exceptions.API10013Error:
            raise Exception(
                "Current session is invalid, "
                "please logout and login again."
            )
        except exceptions.APITimeoutError as e:
            logger.exception(
                "APITimeoutError: {}".format(e)
            )
            raise Exception("Connection timeout, unable to reach API.")
        except exceptions.ProtonSessionWrapperError as e:
            raise Exception("Unknown API error occured: {}".format(e.error))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}.".format(e))

    def __setup_dbus_vpn_monitor(self, dbus_response):
        DBusGMainLoop(set_as_default=True)
        self.dbus_loop = GLib.MainLoop()
        self.__vpn_monitor_connection_start.setup_monitor(
            VIRTUAL_DEVICE_NAME, self.dbus_loop,
            self.__ks_manager, self.__user_conf_manager,
            self.__connection_manager, self.__reconector_manager,
            self.__user_session, dbus_response
        )

    def __start_dbus_vpn_monitor(self):
        self.__vpn_monitor_connection_start.start_monitor()
        self.dbus_loop.run()
