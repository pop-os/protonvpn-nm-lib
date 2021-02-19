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


class KillSwitchManagerActionEnum(Enum):
    PRE_CONNECTION = "pre_connection",
    POST_CONNECTION = "post_connection",
    SOFT = "soft_connection"
    ENABLE = "enable"
    DISABLE = "disable"


class DaemonReconnectorEnum(Enum):
    STOP = "stop"
    START = "start"
    DAEMON_RELOAD = "daemon-reload"


class JsonDataEnumAction(Enum):
    LOAD = 0
    SAVE = 1
