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
    PLUS = 2
    VISIONARY = 2
    PLUS_VISIONARY = 2
    PM = 3


class ConnectionMetadataEnum(Enum):
    SERVER = "connected_server"
    CONNECTED_TIME = "connected_time"
    PROTOCOL = "connected_protocol"


class LastConnectionMetadataEnum(Enum):
    SERVER = ConnectionMetadataEnum.SERVER
    PROTOCOL = ConnectionMetadataEnum.PROTOCOL
    SERVER_IP = "last_connect_ip"


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


class UserSettingEnum(Enum):
    GENERAL = "general"
    CONNECTION = "connection"
    TRAY = "tray"
    ADVANCED = "advanced"


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
    MALWARE = ClientSuffixEnum.NETSHIELD
    ADS_MALWARE = ClientSuffixEnum.NETSHIELD_ADS_TRACKING


class NetshieldTranslationEnum(Enum):
    DISABLED = UserSettingStatusEnum.DISABLED
    MALWARE = UserSettingStatusEnum.ENABLED
    ADS_MALWARE = UserSettingStatusEnum.CUSTOM


class UserSettingConnectionEnum(Enum):
    DEFAULT_PROTOCOL = "default_protocol"
    KILLSWITCH = "killswitch"
    DNS = "dns"
    DNS_STATUS = "status"
    CUSTOM_DNS = "custom_dns"
    SPLIT_TUNNELING = "split_tunneling"
    SPLIT_TUNNELING_STATUS = "status"
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
