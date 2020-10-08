class ProtocolEnum(object):
    TCP = "tcp"
    UDP = "udp"
    IKEV2 = "ikev2"
    WIREGUARD = "wireguard"


class ProtocolImplementationEnum(object):
    OPENVPN = "openvpn"
    STRONGSWAN = "strongswan"
    WIREGUARD = "wireguard"


class ProtocolPortEnum(object):
    TCP = 443
    UDP = 1194


class FeatureEnum(object):
    NORMAL = 0
    SECURE_CORE = 1
    TOR = 2
    P2P = 4
    STREAMING = 8
    IPv6 = 16


class ConnectionMetadataEnum(object):
    SERVER = "connected_server"
    CONNECTED_TIME = "connected_time"
    PROTOCOL = "connected_protocol"


class ClientSuffixEnum(object):
    PLATFORM = "pl"
    NETSHIELD = "f1"
    NETSHIELD_ADS_TRACKING = "f2"
    NETSHIELD_NA = "f3"
    RANDOMAZIED_NAT = "nr"


class KeyringEnum(object):
    DEFAULT_KEYRING_SERVICE = "ProtonVPN"
    DEFAULT_KEYRING_SESSIONDATA = "SessionData"
    DEFAULT_KEYRING_USERDATA = "UserData"
    DEFAULT_KEYRING_PROTON_USER = "ProtonUser"
