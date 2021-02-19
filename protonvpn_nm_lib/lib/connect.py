from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from .. import exceptions
from ..constants import FLAT_SUPPORTED_PROTOCOLS, VIRTUAL_DEVICE_NAME
from ..country_codes import country_codes
from ..enums import (ConnectionTypeEnum, NetworkManagerConnectionTypeEnum,
                     ProtocolEnum)
from ..logger import logger
from ..services.certificate_manager import CertificateManager


class Connect():
    """Connect Class

    Exposes two methods, setup_connection and connect.
    Before attempting to connect(), a user should first
    attempt to setup the connection. Once the connection has
    been successfully setup, the user can proceed to start
    the vpn connection.
    """
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
        dbus_response = {"dbus_response": ""}
        self.connection_manager.start_connection()
        self.__setup_dbus_vpn_monitor(dbus_response)
        self.__start_dbus_vpn_monitor()
        return dbus_response.get(
            "dbus_response", "Something went wrong (x99)"
        )

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
            and not self.__check_country_exists(connection_type_extra_arg)
        ):
            raise exceptions.InvalidCountryCode(
                "The provided country code \"{}\" is invalid.".format(
                    connection_type_extra_arg
                )
            )

        self.connection_type = connection_type
        self.connection_type_extra_arg = connection_type_extra_arg

        if servername: self.__validate_servername(servername)

        # Public method providade by protonvpn_lib
        self._set_self_session()
        # Public method providade by protonvpn_lib
        self._validate_session()

        self.protocol = protocol
        if not self.__is_protocol_valid() or self.protocol is None:
            self.protocol = ProtocolEnum(
                self.user_conf_manager.default_protocol
            )
        logger.info("Setup protocol: {}".format(protocol))

        self.server_manager.killswitch_status = self.user_conf_manager.killswitch # noqa
        logger.info("Setup killswitch user setting")

        # Public method providade by protonvpn_lib
        self._check_connectivity()
        logger.info("Checked for interet and api connectivity")

        # Public method providade by protonvpn_lib
        self._remove_existing_connection()
        logger.info("Removed any possible existing connection")

        openvpn_username, openvpn_password = self.__get_ovpn_credentials()
        logger.info("OpenVPN credentials collected")

        connection_info = self.__add_connection(
            openvpn_username, openvpn_password
        )

        logger.info("Returning connection information")
        return connection_info

    def __check_country_exists(self, country_code):
        if country_code not in country_codes:
            return False

        return True

    def __validate_servername(self, servername):
        if (
            not self.server_manager.is_servername_valid(servername)
        ):
            raise Exception(
                "IllegalServername: Invalid servername {}".format(
                    servername
                )
            )

    def __is_protocol_valid(self):
        """Check if provided protocol is a valid protocol."""
        logger.info("Checking if protocol is valid")
        try:
            self.protocol = ProtocolEnum(self.protocol)
        except ValueError:
            return False

        if self.protocol in FLAT_SUPPORTED_PROTOCOLS:
            return True

        return False

    def __add_connection(self, openvpn_username, openvpn_password):
        # Public method providade by protonvpn_lib
        self._refresh_servers()
        (
            servername, domain,
            server_feature,
            filtered_servers, servers
        ) = self.__get_connection_configurations()

        logger.info("Generated connection configuration.")

        (
            certificate_fp,
            matching_domain,
            entry_ip,
            server_label
        ) = self.server_manager.generate_server_certificate(
            servername, domain, server_feature,
            self.protocol, servers, filtered_servers
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

        connection_info = self._get_connection_metadata(
            NetworkManagerConnectionTypeEnum.ALL
        )

        return connection_info

    def __add_vpn_connection_to_nm(
        self, certificate_filename, openvpn_username,
        openvpn_password, domain, entry_ip
    ):
        """Proxymethod to add ProtonVPN connection."""
        try:
            self.connection_manager.add_connection(
                certificate_filename, openvpn_username, openvpn_password,
                CertificateManager.delete_cached_certificate, domain,
                self.user_conf_manager, self.ks_manager, self.ipv6_lp_manager,
                entry_ip
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
        """Proxymethod to get user OVPN credentials."""
        logger.info("Getting openvpn credentials")

        try:
            if retry:
                self.user_manager.cache_user_data()
            return self.user_manager.get_stored_vpn_credentials( # noqa
                self.session
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

    def __get_connection_configurations(self):
        """Proxymethod to get certficate filename and server domain."""
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
            return self.CONNECT_TYPE_DICT[self.connection_type](
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
        self.vpn_monitor_connection_start.setup_monitor(
            VIRTUAL_DEVICE_NAME, self.dbus_loop,
            self.ks_manager, self.user_conf_manager,
            self.connection_manager, self.reconector_manager,
            self.session, dbus_response
        )

    def __start_dbus_vpn_monitor(self):
        self.vpn_monitor_connection_start.start_monitor()
        self.dbus_loop.run()
