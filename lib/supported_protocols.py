class ProtocolEnum(object):
    TCP = "tcp"
    UDP = "udp"
    IKEV2 = "ikev2"
    WIREGUARD = "wireguard"


class SupportedProtocolEnum(object):
    OPENVPN = [
        ProtocolEnum.TCP,
        ProtocolEnum.UDP
    ]
    STRONGSWAN = ProtocolEnum.IKEV2
    WIREGUARD = ProtocolEnum.WIREGUARD


class ProtocolImplementationEnum(object):
    OPENVPN = "openvpn"
    STRONGSWAN = "strongswan"
    WIREGUARD = "wireguard"