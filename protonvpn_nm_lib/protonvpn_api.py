from .core.certificate import Certificate
from .core.connection_manager import ConnectionManager
from .core.dbus_dbus_monitor_vpn_connection_start import \
    MonitorVPNConnectionStart
from .core.connection_metadata import ConnectionMetadata
from .core.ipv6_leak_protection import IPv6LeakProtection
from .core.killswitch import KillSwitch
from .core.dbus_reconnect import DbusReconnect
from .core.server_manager import ServerManager
from .core.user_configuration_manager import UserConfigurationManager
from .core.user_manager import UserManager
from .enums import UserSettingStatusEnum
from .lib.connect import ProtonVPNConnect
from .lib.connection import ProtonVPNConnection
from .lib.country import ProtonVPNCountry
from .lib.disconnect import ProtonVPNDisconnect
from .lib.login import ProtonVPNLogin
from .lib.logout import ProtonVPNLogout
from .lib.reconnect import ProtonVPNReconnect
from .lib.server import ProtonVPNServer
from .lib.server_list import ProtonVPNServerList
from .lib.session import ProtonVPNSession
from .lib.status import ProtonVPNStatus
from .lib.user_settings import ProtonVPNUserSetting


class API():
    # core
    __connection_metadata = ConnectionMetadata()
    __reconector_manager = DbusReconnect()
    __user_conf_manager = UserConfigurationManager()
    __killswitch = KillSwitch(__user_conf_manager)
    __connection_manager = ConnectionManager()
    __user_manager = UserManager(__user_conf_manager)
    __server_manager = ServerManager(
        Certificate(), __user_manager
    )
    __ipv6_leak_protection = IPv6LeakProtection()

    # library
    country = ProtonVPNCountry(__server_manager)
    connection = ProtonVPNConnection(
        __connection_manager, __connection_metadata
    )
    session = ProtonVPNSession(
        __user_manager,
        __user_conf_manager,
        __connection_manager
    )
    server = ProtonVPNServer(__server_manager, connection)
    server_list = ProtonVPNServerList(
        connection, session, server, country,
        __server_manager, __user_conf_manager
    )
    disconnect = ProtonVPNDisconnect(
        __connection_manager, __user_conf_manager,
        __ipv6_leak_protection, __reconector_manager,
        __killswitch
    )
    connect = ProtonVPNConnect(
        connection, session,
        server, server_list, disconnect, country,
        __connection_manager, __server_manager,
        __user_manager, __user_conf_manager,
        __killswitch, MonitorVPNConnectionStart(),
        __ipv6_leak_protection, __reconector_manager
    )
    reconnect = ProtonVPNReconnect(
        connect, __server_manager, __user_conf_manager
    )
    user_settings = ProtonVPNUserSetting(
        __user_conf_manager, __user_manager, __killswitch
    )
    status = ProtonVPNStatus(
        connection, server, server_list,
        __killswitch, user_settings, __user_conf_manager
    )
    login = ProtonVPNLogin(
        connection, session,
        __server_manager, __user_manager, __user_conf_manager
    )
    logout = ProtonVPNLogout(connection, session, disconnect, __user_manager)

    # Login
    def _login(self, username, password):
        """Login user with provided username and password.
        If login is unsuccessful, an exception will be thrown.
        The exception message will contain necessary

        Args:
        ---
            username (string)
            password (string)
        """
        self.login._login(username, password)

    def _ensure_username_is_valid(self, username):
        """Ensure that the provided username is valid."""
        self.login._ensure_username_is_valid(username)

    # Logout
    def _logout(self):
        """Logout user and delete current user session."""
        self.logout._logout()

    # Connect
    def _setup_connection(
        self, connection_type,
        connection_type_extra_arg=None,
        protocol=None
    ):
        """Setup and configure VPN connection prior
        calling protonvpn._connect().

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
            dict: connection information.
        """
        return self.connect._setup_connection(
            connection_type,
            connection_type_extra_arg,
            protocol
        )

    def _connect(self):
        """Connect to ProtonVPN.

        Should be user either after protonvpn._setup_connection() or
        protonvpn._setup_reconnection().
        """
        return self.connect._connect()

    def _is_protocol_valid(self, protocol):
        """Checks if provided protocol is a valid protocol.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Args:
            protocol (ProtocolEnum)

        Returns:
            bool
        """
        self.connect._is_protocol_valid()

    # Connection
    def _get_active_connection_metadata(self):
        """Get metadata of an active ProtonVPN connection.

        Returns:
            dict
        """
        return self.connection._get_connection_metadata()

    def _get_protonvpn_connection(self, nm_connection_type):
        """Get ProtonVPN connection object.

        Args:
            nm_connection_type (NetworkManagerConnectionTypeEnum)
        Returns:
            list
        """
        return self.connection._get_protonvpn_connection(nm_connection_type)

    def _ensure_connectivity(self):
        """Check for connectivity.

        1) It checks if there is internet connection
        2) It checks if API can be reached

        This is checked during protonvpn._login(),
        protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.
        """
        self.session._ensure_connectivity()

    # Disconnect
    def _disconnect(self):
        """Disconnect from ProtonVPN."""
        self.disconnect._disconnect()

    # Reconnect
    def _setup_reconnection(self):
        """Setup and configure VPN connection to
        a previously connected server.

        Should be called before calling protonvpn._connect().

        Returns:
            dict: connection information.
        """
        return self.reconnect._setup_reconnection()

    # Session
    def _get_session(self):
        """Get user session.

        This is fetched during protonvpn._login(),
        protonvpn._logout(), protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Returns:
            ProtonSessionWrapper
        """
        return self.session._get_session()

    def _check_session_exists(self):
        """Check if sessions exists.

        This is checked during protonvpn._login()
        and protonvpn._logout(), protonvpn._setup_connection()
        and protonvpn._setup_reconnection().

        Can be used whenever needed.

        Returns:
            bool
        """
        return self.session._check_session_exists()

    def _ensure_session_is_valid(self, session):
        """Ensure that provided session is valid.

        This is checked during protonvpn._setup_connection(),
        protonvpn._setup_reconnection().

        Args:
            session (proton.api.Session): user session
        """
        self.session._ensure_session_is_valid(session)

    # Server
    def _ensure_servername_is_valid(self, servername):
        """Ensures if the provided servername is valid.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Args:
            servername (string)
        """
        self.server._ensure_servername_is_valid(servername)

    def _get_country_name(self, country_code):
        """Get country name of a given country code.

        Args:
            country_code (string): ISO format
        """
        return self.country.extract_country_name(country_code)

    def _ensure_country_exists(self, country_code):
        """Checks if given country code exists.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Throws ValueError if country is not found for the
        given country code.

        Args:
            country_code (string): ISO format

        """
        return self.server_list._ensure_country_exists(country_code)

    def _get_filtered_server_list(
        self, server_list, exclude_features=None, include_features=None,
        country_code=None, ignore_tier=False,
        ignore_server_status=False

    ):
        """Get filtered server list.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Args:
            server_list (list(dict))
            exclude_features (list): [FeatureEnum.TOR, ...] (optional)
            include_features (list): [FeatureEnum.TOR, ...] (optional)
                exclude_features and include_features are mutually exclusive.
            country_code (string): country code PT|SE|CH (optional)
                returns servers belonging to specifiec country list.
            ignore_tier (bool): if user tier should be ignored. Filtering
                will not take into consideration the user tier. (optional)
            ignore_server_status (bool): if logical server status is to be
                ignored. If it is ignored, then servers that are unavaliable
                will be returned. (optional)

        Returns:
            list(dict)
        """
        return self.server_list._get_filtered_server_list(
            server_list, exclude_features=exclude_features,
            include_features=include_features,
            country_code=country_code,
            ignore_tier=ignore_tier,
            ignore_server_status=ignore_server_status
        )

    def _get_server_list(self):
        """Get server list.

        It does not cache servers by itself, so running
        protonvpn._refresh_servers() beforehand is strongly
        recommended.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Returns:
            list(dict)
        """
        return self.server_list._get_server_list()

    def _get_country_with_matching_servername(self, server_list):
        """Generate dict with {country:[servername]}.

        Args:
            server_list (list)
        Returns:
            dict: country_code: [servername]
                ie {PT: [PT#5, PT#8]}
        """
        return self.server_list._get_dict_with_country_servername(
            server_list
        )

    def _get_server_information(self, servername):
        """Get server information.

        It does not cache servers, so running
        protonvpn._refresh_servers() should be run
        beforehand in case there is no previous cache.

        Args:
            servername (string)

        Returns:
            Server instance
        """
        return self.server._get_server_information(
            server_list=self._get_server_list(),
            servername=servername,
        )

    def _refresh_servers(self):
        """Refresh cached server list.

        This is fetched during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.
        """
        self.server_list._refresh_servers()

    # Status
    def _get_active_connection_status(self, readeable_format=True):
        """Get active connection status.

        Args:
            readeable_format (bool):
                If true then all content will be returned in
                human readeable format, else all content is returned in
                enum objects.

        Returns:
            dict
        """
        return self.status._get_active_connection_status(readeable_format)

    def _convert_time_from_epoch(self, seconds_since_epoch):
        """Convert time from epoch to 24h.

        Args:
           time_in_epoch (string): time in seconds since epoch

        Returns:
            string: time in 24h format, since last connection was made
        """
        return self.status._convert_time_from_epoch(seconds_since_epoch)

    # User Settings Getter
    def _get_user_settings(self, readeable_format=True):
        """Get user settings.

        Args:
            readeable_format (bool):
                If true then all content will be returnes in
                human readeable format, else all content is returned in
                enum objects.

        Returns:
            dict:
                Keys: DisplayUserSettingsEnum
        """
        return self.user_settings._get_user_settings(readeable_format)

    def _get_netshield(self):
        """Get user netshield setting.

        Returns:
            NetshieldStatusEnum
        """
        return self.user_settings._get_netshield()

    def _get_killswitch(self):
        """Get user Kill Switch setting.

        Returns:
            KillswitchStatusEnum
        """
        return self.user_settings._get_killswitch()

    def _get_protocol(self):
        """Get user set default protocol.

        Returns:
            ProtocolEnum
        """
        return self.user_settings._get_protocol()

    def _get_dns(self):
        """Get user DNS setting.

        Returns:
            UserSettingStatusEnum
        """
        return self.user_settings._get_dns()

    def _get_custom_dns(self):
        """Get user custom DNS servers.

        Returns:
            list
        """
        return self.user_settings._get_custom_dns_list()

    def _get_user_tier(self):
        """Get stored user tier.

        Returns:
            UserTierEnum
        """
        return self.user_settings._get_user_tier()

    # User Settings Setter
    def _set_netshield(self, netshield_enum):
        """Set netshield to specified option.

        Args:
            netshield_enum (NetshieldTranslationEnum)
        """
        self.user_settings._set_netshield(netshield_enum)

    def _set_killswitch(self, killswitch_enum):
        """Set Kill Switch to specified option.

        Args:
            killswitch_enum (KillswitchStatusEnum)
        """
        self.user_settings._set_killswitch(killswitch_enum)

    def _set_protocol(self, protocol_enum):
        """Set default protocol to specified option.

        Args:
            protocol_enum (ProtocolEnum)
        """
        self.user_settings._set_protocol(protocol_enum)

    def _set_automatic_dns(self):
        """Set DNS to be managed automatically by ProtonVPN."""
        self.user_settings._set_dns(
            UserSettingStatusEnum.ENABLED
        )

    def _set_custom_dns(self, dns_ip_list):
        """Set DNS to be managed by custom servers.

        Args:
            dns_ip_list (list)
        """
        self.user_settings._set_dns(
            UserSettingStatusEnum.CUSTOM,
            dns_ip_list
        )

    # User Settings
    def _is_valid_dns_ipv4(self, dns_server_ip):
        """Check if provided IP is valid.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Args:
            dns_server_ip (string): IPv4

        Returns:
            bool
        """
        return self.user_settings._is_valid_ip(dns_server_ip)

    def _reset_to_default_configs(self):
        """Reset user configuration to default values."""
        self.user_settings._reset_to_default_configs()
