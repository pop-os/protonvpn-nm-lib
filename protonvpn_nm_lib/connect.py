from . import exceptions
from .constants import FLAT_SUPPORTED_PROTOCOLS
from .logger import logger
from .services.certificate_manager import CertificateManager


class Connect():
    """Connect Class

    Exposes two methods, setup_connection and connect.
    Before attempting to connect(), a user should first
    attempt to setup the connection. Once the connection has
    been successfully setup, the user can proceed to start
    the vpn connection.
    """
    def _connect(self):
        """Connect to VPN."""
        dbus_response = {"dbus_response": ""}
        self.connection_manager.start_connection()
        self.setup_dbus_vpn_monitor(dbus_response)
        self.start_dbus_vpn_monitor()
        return dbus_response.get(
            "dbus_response", "Something went wrong (x99)"
        )

    def setup_connection(self, servername=None, protocol=None):
        """Setup VPN connection.

        Args:
            servername (string): [PT#9]
                (optional) should be passed only when
                connecting to a specific server.
            optional protocol (ProtocolEnum): ProtocolEnum.TPC
                (optional) if None, then protocol will be fetched
                from user configurations.

        Returns:
            dict: contains connection information to be displayes for user.
        """
        if servername: self.validate_servername(servername)
        self.get_existing_session()
        self.__validate_session()

        self.protocol = protocol
        if not self.is_protocol_valid() or self.protocol is None:
            self.protocol = self.user_conf_manager.default_protocol
        logger.info("Setup protocol: {}".format(protocol))

        self.server_manager.killswitch_status = self.user_conf_manager.killswitch # noqa
        logger.info("Setup killswitch user setting")
        self.check_connectivity()
        logger.info("Checked for interet and api connectivity")
        self.remove_existing_connection()
        logger.info("Removed any possible existing connection")

        openvpn_username, openvpn_password = self.__get_ovpn_credentials()
        logger.info("OpenVPN credentials collected")

        connection_info = self.__add_connection(
            openvpn_username, openvpn_password
        )

        return connection_info

    def validate_servername(self, servername):
        if (
            not self.server_manager.is_servername_valid(servername)
        ):
            raise Exception(
                "IllegalServername: Invalid servername {}".format(
                    servername
                )
            )

    def __validate_session(self):
        try:
            self.server_manager.validate_session(self.session)
        except Exception as e:
            raise Exception(e)

    def is_protocol_valid(self):
        """Check if provided protocol is a valid protocol."""
        logger.info("Checking if protocol is valid")
        if self.protocol in FLAT_SUPPORTED_PROTOCOLS:
            return True

        return False

    def __add_connection(self, openvpn_username, openvpn_password):
        self.refresh_servers(self.session)
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

        connection_info = self.connection_manager.display_connection_status(
            "all_connections"
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
                self.connect_type,
                type(self.connect_type),
            )
        )
        logger.info(
            "Connect type extra arg: {} - {}".format(
                self.connect_type_extra_arg,
                type(self.connect_type_extra_arg),
            )
        )
        try:
            return self.CONNECT_TYPE_DICT[self.connect_type](
                self.session,
                self.connect_type_extra_arg
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
