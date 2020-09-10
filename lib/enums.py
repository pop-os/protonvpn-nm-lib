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
