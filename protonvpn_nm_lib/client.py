from . import exceptions
from .enums import (ConnectionMetadataEnum, ConnectionTypeEnum,
                    DbusMonitorResponseEnum, KillswitchStatusEnum,
                    MetadataEnum)
from .init import (connection, connection_metadata, country, protonvpn_user,
                   server_configurator, server_filter, server_list, session,
                   status, utils, vpn_certificate)
from .logger import logger
from .monitor_connection_start import (setup_dbus_vpn_monitor,
                                       start_dbus_vpn_monitor)


class Client:

    def login(self, username, password):
        """Login user with provided username and password.
        If login is unsuccessful, an exception will be thrown.

        Args:
            username (string)
            password (string)
        """
        utils.ensure_connectivity(protonvpn_user.settings.killswitch)
        session.login(username, password)

    def logout(self):
        """Logout user and delete current user session."""
        try:
            self.disconnect()
        except exceptions.ConnectionNotFound:
            pass
        session.logout()

    def connect(self):
        """Connect to ProtonVPN.

        Should be user either after setup_connection() or
        setup_reconnect_to_previously_connected_server().
        """
        dbus_response = {DbusMonitorResponseEnum.RESPONSE: ""}
        utils.ensure_internet_connection_is_available(
            protonvpn_user.settings.killswitch
        )

        connection.connect()
        setup_dbus_vpn_monitor(dbus_response)
        start_dbus_vpn_monitor()
        connection_metadata.save_connected_time()
        return dbus_response

    def disconnect(self):
        """Disconnect from ProtonVPN"""
        connection.disconnect()

    def setup_connection(
        self,
        connection_type,
        connection_type_extra_arg=None,
        protocol=None
    ):
        """Setup and configure VPN connection prior
        calling connect().

        Args:
            connection_type (ConnectionTypeEnum):
                selected connection type
            connection_type_extra_arg (string):
                (optional) should be used only when
                connecting directly to a specific server
                with ConnectionTypeEnum.SERVERNAME or when
                connecting to a specific country with
                ConnectionTypeEnum.COUNTRY.
            optional protocol (string):
                (optional) if None, then protocol will be fetched
                from user configurations.

        Returns:
            dict: dbus response
        """
        if not session.check_session_exists():
            raise exceptions.UserSessionNotFound(
                "User session was not found, please login first."
            )
        killswitch_status = protonvpn_user.settings.killswitch
        utils.ensure_connectivity(killswitch_status)
        connect_configurations = {
            ConnectionTypeEnum.SERVERNAME:
                self.config_for_server_with_servername,
            ConnectionTypeEnum.FASTEST: self.config_for_fastest_server,
            ConnectionTypeEnum.RANDOM: self.config_for_random_server,
            ConnectionTypeEnum.COUNTRY:
                self.config_for_fastest_server_in_country,
            ConnectionTypeEnum.SECURE_CORE:
                self.config_for_fastest_server_with_feature,
            ConnectionTypeEnum.PEER2PEER:
                self.config_for_fastest_server_with_feature,
            ConnectionTypeEnum.TOR: self.config_for_fastest_server_with_feature
        }
        (
            _connection_type,
            _connection_type_extra_arg,
            _protocol
        ) = utils.parse_user_input(
            {
                "connection_type": connection_type,
                "connection_type_extra_arg": connection_type_extra_arg,
                "protocol": protocol,
            },
            country.ensure_country_code_exists,
            protonvpn_user.settings.protocol
        )

        try:
            self.disconnect()
        except exceptions.ConnectionNotFound:
            pass

        if killswitch_status != KillswitchStatusEnum.HARD:
            session.refresh_servers()

        server = connect_configurations[connection_type](
            _connection_type_extra_arg,
        )

        physical_server = server_list.get_random_physical_server(server)
        certificate_path = vpn_certificate.generate(
            _protocol, server.name, [physical_server.entry_ip]
        )

        openvpn_username = protonvpn_user.ovpn_username
        if physical_server.label is not None:
            openvpn_username = openvpn_username + "+b:" + physical_server.label
            logger.info("Appended server label.")

        server_data = {
            "domain": physical_server.domain,
            "server_entry_ip": physical_server.entry_ip,
            "servername": server.name
        }
        user_data = {
            "dns": {
                "dns_status": protonvpn_user.settings.dns,
                "custom_dns": protonvpn_user.settings.dns_custom_ips
            },
            "credentials": {
                "ovpn_username": openvpn_username,
                "ovpn_password": protonvpn_user.ovpn_password
            },
        }
        utils.post_setup_connection_save_metadata(
            connection_metadata, server.name,
            _protocol, physical_server
        )
        connection.adapter.certificate_filepath = certificate_path
        connection.setup_connection(server_data, user_data)

    def config_for_fastest_server(self, *_):
        """Select fastest server.

        Returns:
            LogicalServer
        """
        return server_configurator.get_config_for_fastest_server()

    def config_for_fastest_server_in_country(self, country_code):
        """Select server by country code.

        Returns:
            LogicalServer
        """
        return server_configurator.get_config_for_fastest_server_in_country(
            country_code
        )

    def config_for_fastest_server_with_feature(self, feature):
        """Select server by specified feature.

        Returns:
            LogicalServer
        """
        return server_configurator.\
            get_config_for_fastest_server_with_specific_feature(feature)

    def config_for_server_with_servername(self, servername):
        """Select server by servername.

        Returns:
            LogicalServer
        """
        return server_configurator.get_config_for_specific_server(
            servername
        )

    def config_for_random_server(self, *_):
        """Select server for random connection.

        Returns:
            LogicalServer
        """
        return server_configurator.get_config_for_random_server()

    def setup_reconnect(self):
        """Setup and configure VPN connection to
        a previously connected server.

        Should be called before calling connect().
        """
        logger.info("Attemtping to recconnect to previous server")
        last_connection_metadata = connection_metadata.get_connection_metadata(
            MetadataEnum.LAST_CONNECTION
        )

        try:
            previous_server = last_connection_metadata[
                ConnectionMetadataEnum.SERVER.value
            ]
        except KeyError:
            logger.error(
                "File exists but servername field is missing, exitting"
            )
            raise Exception(
                "No previous connection data was found, "
                "please first connect to a server."
            )

        try:
            protocol = last_connection_metadata[
                ConnectionMetadataEnum.PROTOCOL.value
            ]
        except KeyError:
            protocol = None

        logger.info("Passed all check, will reconnecto to \"{}\"".format(
            previous_server
        ))

        self.setup_connection(
            connection_type=ConnectionTypeEnum.SERVERNAME,
            connection_type_extra_arg=previous_server,
            protocol=protocol
        )

    def get_user(self):
        """Get user."""
        return protonvpn_user

    def get_user_settings(self):
        """Get user settings"""
        return protonvpn_user.settings

    def get_session(self):
        """Get user session.

        This can be used for the following purposes:
            - login
            - logout
            - refresh server cache
            - check if session exists

        Returns:
            Session
        """
        return session

    def check_session_exists(self):
        """Checks if session exists.

        Returns:
            bool
        """
        return session.check_session_exists()

    def get_connection_status(self):
        """Get active connection status.

        Args:
            readeable_format (bool):
                If true then all content will be returned in
                human readeable format, else all content is returned in
                enum objects.

        Returns:
            dict
        """
        return status.get_active_connection_status()

    def get_connection_metadata(self):
        """Get metadata of an active ProtonVPN connection.

        Returns:
            dict
        """
        return connection_metadata.get_connection_metadata(
            MetadataEnum.CONNECTION
        )

    def get_non_active_protonvpn_connection(self):
        """Get non active ProtonVPN connection object.

        Args:
            nm_connection_type (NetworkManagerConnectionTypeEnum)
        Returns:
            VPN connection
        """
        return connection.get_non_active_protonvpn_connection()

    def get_active_protonvpn_connection(self):
        """Get active ProtonVPN connection object.

        Args:
            nm_connection_type (NetworkManagerConnectionTypeEnum)
        Returns:
            VPN connection
        """
        return connection.get_active_protonvpn_connection()

    def ensure_connectivity(self):
        """Check for connectivity.

        1) It checks if there is internet connection
        2) It checks if API can be reached
        """
        utils.ensure_connectivity(protonvpn_user.settings.killswitch)

    def get_country(self):
        """Get country object.

        Args:
            Country
        """
        return country

    def get_server_list(self):
        """Get server list object.

        Returns:
            ServerList
        """
        return server_list

    def get_server_filter(self):
        """Get server filter object.

        Returns:
            ServerFilter
        """
        return server_filter
