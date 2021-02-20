from .enums import UserSettingStatusEnum
from .lib.connect import ProtonVPNConnect
from .lib.connection import ProtonVPNConnection
from .lib.disconnect import ProtonVPNDisconnect
from .lib.login import ProtonVPNLogin
from .lib.logout import ProtonVPNLogout
from .lib.reconnect import ProtonVPNReconnect
from .lib.server import ProtonVPNServer
from .lib.session import ProtonVPNSession
from .lib.status import ProtonVPNStatus
from .lib.user_settings import ProtonVPNUserSetting
from .services.certificate_manager import CertificateManager
from .services.connection_manager import ConnectionManager
from .services.dbus_dbus_monitor_vpn_connection_start import \
    MonitorVPNConnectionStart
from .services.ipv6_leak_protection_manager import IPv6LeakProtectionManager
from .services.killswitch_manager import KillSwitchManager
from .services.reconnector_manager import ReconnectorManager
from .services.server_manager import ServerManager
from .services.user_configuration_manager import UserConfigurationManager
from .services.user_manager import UserManager


class API():
    # services
    reconector_manager = ReconnectorManager()
    user_conf_manager = UserConfigurationManager()
    ks_manager = KillSwitchManager(user_conf_manager)
    connection_manager = ConnectionManager()
    user_manager = UserManager(user_conf_manager)
    server_manager = ServerManager(
        CertificateManager(), user_manager
    )
    ipv6_lp_manager = IPv6LeakProtectionManager()

    # library
    connection = ProtonVPNConnection(
        connection_manager,
        user_conf_manager,
        ks_manager,
        ipv6_lp_manager,
        reconector_manager
    )
    session = ProtonVPNSession(user_manager)
    server = ProtonVPNServer(
        connection, session,
        server_manager, user_conf_manager
    )
    connect = ProtonVPNConnect(
        connection, session, server,
        connection_manager, server_manager,
        user_manager, user_conf_manager,
        ks_manager, MonitorVPNConnectionStart(),
        ipv6_lp_manager, reconector_manager
    )
    disconnect = ProtonVPNDisconnect(
        connection_manager, user_conf_manager,
        ipv6_lp_manager, reconector_manager,
        ks_manager
    )
    reconnect = ProtonVPNReconnect(connect, server_manager, user_conf_manager)
    user_settings = ProtonVPNUserSetting(
        user_conf_manager, user_manager, ks_manager
    )
    status = ProtonVPNStatus(
        connection, server,
        ks_manager, user_settings, user_conf_manager
    )
    login = ProtonVPNLogin(
        connection, server_manager, user_manager, user_conf_manager
    )
    logout = ProtonVPNLogout(connection, session, user_manager)

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
        connection_type_extra_arg, protocol
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
            tuple
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
        self.connection._ensure_connectivity()

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
        return self.server.extract_country_name(country_code)

    def _check_country_exists(self, country_code):
        """Checks if given country code exists.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Args:
            country_code (string): ISO format

        Returns:
            bool
        """
        return self.server._check_country_exists(country_code)

    def _get_filtered_servers(self, server_list):
        """Get filtered server list.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Args:
            server_list (list(dict))

        Returns:
            list(dict)
        """
        return self.server._get_filtered_servers(server_list)

    def _get_server_list(self):
        """Get server list.

        This is checked during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.

        Returns:
            list(dict)
        """
        return self.server._get_server_list()

    def _get_country_with_matching_servername(self, server_list):
        """Generate dict with {country:[servername]}.

        Args:
            server_list (list)
        Returns:
            dict: country_code: [servername]
                ie {PT: [PT#5, PT#8]}
        """
        return self.server._get_dict_with_country_servername(
            server_list
        )

    def _get_server_information(self, servername):
        """Get server information.

        Args:
            servername (string)

        Returns:
            dict:
                Keys: ServerInfoEnum
        """
        return self.server._get_server_information(servername)

    def _refresh_servers(self):
        """Refresh cached server list.

        This is fetched during protonvpn._setup_connection()
        and protonvpn._setup_reconnection().
        Can be used whenever needed.
        """
        self.server._refresh_servers()

    # Status
    def _get_active_connection_status(self, readeable_format=True):
        """Get active connection status.

        Args:
            readeable_format (bool):
                If true then all content will be returnes in
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
        return self.user_settings._get_dns(True)

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
