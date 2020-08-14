# https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
# Save settings in XDG_CONFIG_HOME
# Save cache XDG_CACHE_HOME
# Save logs and other user data in XDG_DATA_HOME

import os
from xdg import XDG_CACHE_HOME
# XDG_CONFIG_HOME, XDG_DATA_HOME

PWD = os.path.dirname(os.path.abspath(__file__))

TEMPLATES = os.path.join(PWD, "templates")
OPENVPN_TEMPLATE = "openvpn_template.j2"
PROTON_XDG_CACHE_HOME = os.path.join(XDG_CACHE_HOME, "protonvpn")
CACHED_SERVERLIST = os.path.join(
    PROTON_XDG_CACHE_HOME, "cached_serverlist.json"
)
CACHED_OPENVPN_CERTIFICATE = os.path.join(
    PROTON_XDG_CACHE_HOME, "ProtonVPN.ovpn"
)

DEFAULT_KEYRING_SERVICE = "ProtonVPN"
DEFAULT_KEYRING_USERNAME = "AuthData"
DEV_ENV = os.environ.get("protonvpn_dev")
