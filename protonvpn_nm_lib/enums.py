from enum import Enum


class ProtocolEnum(Enum):
    TCP = "tcp"
    UDP = "udp"
    IKEV2 = "ikev2"
    WIREGUARD = "wireguard"


class ProtocolImplementationEnum(Enum):
    OPENVPN = "openvpn"
    STRONGSWAN = "strongswan"
    WIREGUARD = "wireguard"


class ProtocolPortEnum(Enum):
    TCP = 443
    UDP = 1194


class FeatureEnum(Enum):
    NORMAL = 0
    SECURE_CORE = 1
    TOR = 2
    P2P = 4
    STREAMING = 8
    IPv6 = 16


class ServerTierEnum(Enum):
    FREE = 0
    BASIC = 1
    # PLUS = 2
    # VISIONARY = 2
    PLUS_VISIONARY = 2
    PM = 3


class UserTierEnum(Enum):
    FREE = 0
    BASIC = 1
    PLUS_VISIONARY = 2
    PM = 3


class ConnectionMetadataEnum(Enum):
    SERVER = "connected_server"
    CONNECTED_TIME = "connected_time"
    PROTOCOL = "connected_protocol"
    DISPLAY_SERVER_IP = "display_server_ip"


class LastConnectionMetadataEnum(Enum):
    SERVER = ConnectionMetadataEnum.SERVER.value
    PROTOCOL = ConnectionMetadataEnum.PROTOCOL.value
    SERVER_IP = "last_connect_ip"
    DISPLAY_SERVER_IP = ConnectionMetadataEnum.DISPLAY_SERVER_IP.value


class ClientSuffixEnum(Enum):
    PLATFORM = "pl"
    NETSHIELD = "f1"
    NETSHIELD_ADS_TRACKING = "f2"
    NETSHIELD_NA = "f3"
    RANDOMAZIED_NAT = "nr"


class KeyringEnum(Enum):
    DEFAULT_KEYRING_SERVICE = "ProtonVPN"
    DEFAULT_KEYRING_SESSIONDATA = "SessionData"
    DEFAULT_KEYRING_USERDATA = "UserData"
    DEFAULT_KEYRING_PROTON_USER = "ProtonUser"


class UserSettingStatusEnum(Enum):
    DISABLED = 0
    ENABLED = 1
    CUSTOM = 2


class KillswitchStatusEnum(Enum):
    DISABLED = 0
    HARD = 1
    SOFT = 2


class NetshieldStatusEnum(Enum):
    DISABLED = "f0"
    MALWARE = ClientSuffixEnum.NETSHIELD.value
    ADS_MALWARE = ClientSuffixEnum.NETSHIELD_ADS_TRACKING.value


class NetshieldTranslationEnum(Enum):
    DISABLED = 0
    MALWARE = 1
    ADS_MALWARE = 2


class UserSettingConnectionEnum(Enum):
    DEFAULT_PROTOCOL = "default_protocol"
    KILLSWITCH = "killswitch"
    DNS = "dns"
    DNS_STATUS = "dns_status"
    CUSTOM_DNS = "custom_dns"
    SPLIT_TUNNELING = "split_tunneling"
    SPLIT_TUNNELING_STATUS = "split_tunneling_status"
    IP_LIST = "ip_list"
    NETSHIELD = "netshield"


class ProtonSessionAPIMethodEnum(Enum):
    API_REQUEST = "api_request"
    AUTHENTICATE = "authenticate"
    LOGOUT = "logout"
    FULL_CACHE = "logicals"
    LOADS_CACHE = "loads"


class MetadataActionEnum(Enum):
    GET = "get"
    WRITE = "write"
    REMOVE = "remove"


class MetadataEnum(Enum):
    CONNECTION = "connection_metadata"
    LAST_CONNECTION = "last_connection_metadata"
    SERVER_CACHE = "cache_metadata"


class ConnectionTypeEnum(Enum):
    SERVERNAME = 1
    FASTEST = 2
    RANDOM = 3
    COUNTRY = 4
    SECURE_CORE = 5
    PEER2PEER = 6
    TOR = 7


class NetworkManagerConnectionTypeEnum(Enum):
    ACTIVE = 0
    ALL = 1


class ServerEnum(Enum):
    ID = "ID"
    DOMAIN = "Domain"
    STATUS = "Status"


class LogicalServerEnum(Enum):
    NAME = "Name"
    ENTRY_COUNTRY = "EntryCountry"
    EXIT_COUNTRY = "ExitCountry"
    TIER = "Tier"
    FEATURES = "Features"
    REGION = "Region"
    CITY = "City"
    SCORE = "Score"
    LOCATION = "Location"
    SERVERS = "Servers"
    LOAD = "Load"


class PhysicalServerEnum(Enum):
    ENTRY_IP = "EntryIP"
    EXIT_IP = "ExitIP"
    GENERATION = "Generation"
    SERVICES_DOWN_REASON = "ServicesDownReason"
    LABEL = "Label"


class ServerLocation(Enum):
    LONGITUDE = "Long"
    LATITUDE = "Lat"


class ServerInfoEnum(Enum):
    SERVERNAME = "Servername"
    COUNTRY = "ExitCountry"
    CITY = "City"
    LOAD = "Load"
    TIER = "Tier"
    FEATURES = "Features"
    LOCATION = "Location"
    LATITUDE = "Lat"
    LONGITUDE = "Long"
    ENTRY_COUNTRY = "EntryCountry"
    REGION = "Region"


class ConnectionStatusEnum(Enum):
    SERVER_INFORMATION = "server_information"
    PROTOCOL = "protocol"
    TIME = "time"
    KILLSWITCH = "killswitch"
    NETSHIELD = "netshield"
    SERVER_IP = "server_ip"


class DisplayUserSettingsEnum(Enum):
    PROTOCOL = 0
    KILLSWITCH = 1
    DNS = 2
    CUSTOM_DNS = 3
    NETSHIELD = 4


class KillSwitchInterfaceTrackerEnum(Enum):
    EXISTS = 0
    IS_RUNNING = 1


class KillSwitchActionEnum(Enum):
    PRE_CONNECTION = "pre_connection",
    POST_CONNECTION = "post_connection",
    SOFT = "soft_connection"
    ENABLE = "enable"
    DISABLE = "disable"


class DaemonReconnectorEnum(Enum):
    STOP = "stop"
    START = "start"
    DAEMON_RELOAD = "daemon-reload"


class DbusMonitorResponseEnum(Enum):
    RESPONSE = "dbus_response"
    STATE = "state"
    REASON = "reason"
    MESSAGE = "message"


class DbusVPNConnectionStateEnum(Enum):
    """
    NMVpnConnectionState(int)

    0 (UNKNOWN): The state of the VPN connection is unknown.
    1 (PREPARING_TO_CONNECT): The VPN connection is preparing to connect.
    2 (NEEDS_CREDENTIALS): The VPN connection needs authorization credentials.
    3 (BEING_ESTABLISHED): The VPN connection is being established.
    4 (GETTING_IP_ADDRESS): The VPN connection is getting an IP address.
    5 (IS_ACTIVE): The VPN connection is active.
    6 (FAILED): The VPN connection failed.
    7 (DISCONNECTED): The VPN connection is disconnected.
    999 (UNKNOWN_ERROR): Custom error
    """
    UNKNOWN = 0
    PREPARING_TO_CONNECT = 1
    NEEDS_CREDENTIALS = 2
    BEING_ESTABLISHED = 3
    GETTING_IP_ADDRESS = 4
    IS_ACTIVE = 5
    FAILED = 6
    DISCONNECTED = 7
    UNKNOWN_ERROR = 999


class DbusVPNConnectionReasonEnum(Enum):
    """
    NMActiveConnectionStateReason(int)

    0 (UNKNOWN):  The reason for the active connection state change
            is unknown.
    1 (NOT_PROVIDED):  No reason was given for the
        active connection state change.
    2 (USER_HAS_DISCONNECTED):  The active connection changed state because
        the user disconnected it.
    3 (DEVICE_WAS_DISCONNECTED):  The active connection changed state because
        the device it was using was disconnected.
    4 (SERVICE_PROVIDER_WAS_STOPPED):  The service providing the
        VPN connection was stopped.
    5 (IP_CONFIG_WAS_INVALID):  The IP config of the active
        connection was invalid.
    6 (CONN_ATTEMPT_TO_SERVICE_TIMED_OUT):  The connection attempt
        to the VPN service timed out.
    7 (TIMEOUT_WHILE_STARTING_VPN_SERVICE_PROVIDER):  A timeout occurred while
        starting the service providing the VPN connection.
    8 (START_SERVICE_VPN_CONN_SERVICE_FAILED):  Starting the service
        providing the VPN connection failed.
    9 (SECRETS_WERE_NOT_PROVIDED):  Necessary secrets for the connection
        were not provided.
    10 (SERVER_AUTH_FAILED): Authentication to the server failed.
    11 (DELETED_FROM_SETTINGS): The connection was deleted from settings.
    12 (MASTER_CONN_FAILED_TO_ACTIVATE): Master connection of this
        connection failed to activate.
    13 (CREATE_SOFTWARE_DEVICE_LINK_FAILED): Could not create
        the software device link.
    14 (VPN_DEVICE_DISAPPEARED): The device this connection
        depended on disappeared.
    999 (UNKNOWN_ERROR): Custom error
    """
    UNKNOWN = 0
    NOT_PROVIDED = 1
    USER_HAS_DISCONNECTED = 2
    DEVICE_WAS_DISCONNECTED = 3
    SERVICE_PROVIDER_WAS_STOPPED = 4
    IP_CONFIG_WAS_INVALID = 5
    CONN_ATTEMPT_TO_SERVICE_TIMED_OUT = 6
    TIMEOUT_WHILE_STARTING_VPN_SERVICE_PROVIDER = 7
    START_SERVICE_VPN_CONN_SERVICE_FAILED = 8
    SECRETS_WERE_NOT_PROVIDED = 9
    SERVER_AUTH_FAILED = 10
    DELETED_FROM_SETTINGS = 11
    MASTER_CONN_FAILED_TO_ACTIVATE = 12
    CREATE_SOFTWARE_DEVICE_LINK_FAILED = 13
    VPN_DEVICE_DISAPPEARED = 14
    UNKNOWN_ERROR = 999
