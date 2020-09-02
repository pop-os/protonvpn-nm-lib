# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
# Save settings in XDG_CONFIG_HOME
# Save cache XDG_CACHE_HOME
# Save logs and other user data in XDG_DATA_HOME

import os
from xdg import XDG_CACHE_HOME
# XDG_CONFIG_HOME, XDG_DATA_HOME
from .enums import (
    ProtocolImplementationEnum,
    ProtocolEnum
)

APP_VERSION = '0.0.1'

PWD = os.path.dirname(os.path.abspath(__file__))

TEMPLATES = os.path.join(PWD, "templates")
OPENVPN_TEMPLATE = "openvpn_template.j2"
PROTON_XDG_CACHE_HOME = os.path.join(XDG_CACHE_HOME, "protonvpn")
PROTON_XDG_CACHE_HOME_LOGS = os.path.join(PROTON_XDG_CACHE_HOME, "logs")
CACHED_SERVERLIST = os.path.join(
    PROTON_XDG_CACHE_HOME, "cached_serverlist.json"
)
CACHED_OPENVPN_CERTIFICATE = os.path.join(
    PROTON_XDG_CACHE_HOME, "ProtonVPN.ovpn"
)
LOGFILE = os.path.join(PROTON_XDG_CACHE_HOME_LOGS, "protonvpn.log")
DEFAULT_KEYRING_SERVICE = "ProtonVPN"
DEFAULT_KEYRING_USERNAME = "AuthData"
ENV_CI_NAME = "protonvpn_ci"

SUPPORTED_PROTOCOLS = {
    ProtocolImplementationEnum.OPENVPN: [ProtocolEnum.TCP, ProtocolEnum.UDP],
    # ProtocolImplementationEnum.STRONGSWAN: [ProtocolEnum.IKEV2],
    # ProtocolImplementationEnum.WIREGUARD: [ProtocolEnum.WIREGUARD],
}

VIRTUAL_DEVICE_NAME = "proton0"
