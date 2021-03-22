from . import exceptions
from .core.country import Country
from .core.environment import ExecutionEnvironment
from .core.status import Status
from .core.utilities import Utilities
from .enums import (ConnectionMetadataEnum, ConnectionTypeEnum, FeatureEnum,
                    MetadataEnum)
from .logger import logger


class ProtonVPNClientAPI:
    def __init__(self):
        # The constructor should be where you initialize
        # the environment and it's parameter
        self._env = ExecutionEnvironment()
        self.country = Country()
        self.utils = Utilities
        self.status = Status()

    def login(self, username, password):
        """Login user with provided username and password.
        If login is unsuccessful, an exception will be thrown.

        Args:
            username (string)
            password (string)
        """
        self.utils.ensure_connectivity(self._env.settings.killswitch)
        self._env.api_session.login(username, password)

    def logout(self):
        """Logout user and delete current user session."""

        try:
            self._env.connection_backend.disconnect()
        except exceptions.ConnectionNotFound:
            pass

        self._env.api_session.logout()

    def connect(self):
        """Connect to ProtonVPN.

        Should be user either after setup_connection() or
        setup_reconnect_to_previously_connected_server().
        """
        self.utils.ensure_internet_connection_is_available(
            self._env.settings.killswitch
        )
        connect_result = self._env.connection_backend.connect()
        # print(self._env.connection_metadata.get_connection_metadata(MetadataEnum.CONNECTION))
        self._env.connection_metadata.save_connect_time()
        return connect_result

    def disconnect(self):
        """Disconnect from ProtonVPN"""
        self._env.connection_backend.disconnect()

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
        if not self._env.api_session.is_valid:
            raise exceptions.UserSessionNotFound(
                "User session was not found, please login first."
            )
        self.utils.ensure_connectivity(self._env.settings.killswitch)

        (
            _connection_type,
            _connection_type_extra_arg,
            _protocol
        ) = self.utils.parse_user_input(
            {
                "connection_type": connection_type,
                "connection_type_extra_arg": connection_type_extra_arg,
                "protocol": protocol,
            }
        )
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

        server = connect_configurations[connection_type](
            _connection_type_extra_arg,
        )
        physical_server = server.get_random_physical_server()
        self._env.api_session.servers.match_server_domain(physical_server)

        openvpn_username = self._env.api_session.vpn_username
        if physical_server.label:
            openvpn_username = openvpn_username + "+b:" + physical_server.label
            logger.info("Appended server label.")

        data = {
            "domain": physical_server.domain,
            "entry_ip": physical_server.entry_ip,
            "servername": server.name,
            "credentials": {
                "ovpn_username": openvpn_username,
                "ovpn_password": self._env.api_session.vpn_password
            },
        }
        self._env.connection_metadata.save_servername(server.name)
        self._env.connection_metadata.save_protocol(_protocol)
        self._env.connection_metadata.save_display_server_ip(
            physical_server.exit_ip
        )
        self._env.connection_metadata.save_server_ip(physical_server.entry_ip)

        logger.info("Stored metadata to file")
        configuration = physical_server.get_configuration(_protocol)
        logger.info("Received confiuration object")
        self._env.connection_backend.vpn_configuration = configuration

        logger.info("Setting up {}".format(server.name))
        self._env.connection_backend.setup(**data)

    def config_for_fastest_server(self, *_):
        """Select fastest server.

        Returns:
            LogicalServer
        """
        return self._env.api_session.servers.get_fastest_server()

    def config_for_fastest_server_in_country(self, country_code):
        """Select server by country code.

        Returns:
            LogicalServer
        """
        return self._env.api_session.servers.filter(
            lambda server: server.exit_country.lower() == country_code.lower() # noqa
        ).get_fastest_server()

    def config_for_fastest_server_with_feature(self, feature):
        """Select server by specified feature.

        Returns:
            LogicalServer
        """
        connection_dict = {
            ConnectionTypeEnum.SECURE_CORE: FeatureEnum.SECURE_CORE,
            ConnectionTypeEnum.PEER2PEER: FeatureEnum.P2P,
            ConnectionTypeEnum.TOR: FeatureEnum.TOR,
        }
        return self._env.api_session.servers.filter(
            lambda server: (
                server.features == connection_dict[feature]
            )
        ).get_fastest_server()

    def config_for_server_with_servername(self, servername):
        """Select server by servername.

        Returns:
            LogicalServer
        """
        return self._env.api_session.servers.filter(
            lambda server: server.name.lower() == servername.lower() # noqa
        ).get_fastest_server()

    def config_for_random_server(self, *_):
        """Select server for random connection.

        Returns:
            LogicalServer
        """
        return self._env.api_session.servers.get_random_server()

    def setup_reconnect(self):
        """Setup and configure VPN connection to
        a previously connected server.

        Should be called before calling connect().
        """
        logger.info("Attemtping to recconnect to previous server")
        last_connection_metadata = self._env.connection_metadata\
            .get_connection_metadata(
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

    def check_session_exists(self):
        """Checks if session exists.

        Returns:
            bool
        """
        return self._env.api_session.is_valid

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
        return self.status.get_active_connection_status()

    def get_settings(self):
        """Get user settings."""
        return self._env.settings

    def get_session(self):
        """Get user settings."""
        return self._env.api_session

    def get_country(self):
        """Get country object."""
        return self.country

    def get_connection_metadata(self):
        """Get metadata of an active ProtonVPN connection.

        Returns:
            dict
        """
        return self._env.connection_metadata.get_connection_metadata(
            MetadataEnum.CONNECTION
        )

    def get_non_active_protonvpn_connection(self):
        """Get non active ProtonVPN connection object.

        Args:
            nm_connection_type (NetworkManagerConnectionTypeEnum)
        Returns:
            VPN connection
        """
        return self._env.connection_backend\
            .get_non_active_protonvpn_connection()

    def get_active_protonvpn_connection(self):
        """Get active ProtonVPN connection object.

        Args:
            nm_connection_type (NetworkManagerConnectionTypeEnum)
        Returns:
            VPN connection
        """
        return self._env.connection_backend\
            .get_active_protonvpn_connection()

    def ensure_connectivity(self):
        """Check for connectivity.

        1) It checks if there is internet connection
        2) It checks if API can be reached
        """
        self.utils.ensure_connectivity(
            self._env.settings.killswitch
        )

protonvpn = ProtonVPNClientAPI() # noqa
