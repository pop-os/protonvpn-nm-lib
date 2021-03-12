from .enums import ProtocolEnum, ConnectionTypeEnum
from .constants import VIRTUAL_DEVICE_NAME

# Killswitch
from .core.killswitch import IPv6LeakProtection, KillSwitch
# Session
from .core.session import Session
# User
from .core.user import ProtonVPNUser
# Connection
from .core.connection import VPNCertificate, Connection
# Servers
from .core.servers import ServerList, ServerFilter, ServerConfigurator
# Metadata
from .core.metadata import ConnectionMetadata
# Dbus processes
from .core.dbus import DbusReconnect
# Other
from .core import Country, Utilities


dbus_reconnector = DbusReconnect()
utils = Utilities()

killswitch = KillSwitch()
ipv6_leak_protection = IPv6LeakProtection()

vpn_certificate = VPNCertificate()
server_list = ServerList()
server_filter = ServerFilter()
session = Session()
connection_metadata = ConnectionMetadata()

protonvpn_user = ProtonVPNUser()
protonvpn_user.session = session
protonvpn_user.settings.protonvpn_user = protonvpn_user
protonvpn_user.settings.killswitch_obj = killswitch

country = Country()
server_configurator = ServerConfigurator.init(
    protonvpn_user, server_list, server_filter
)
connection = Connection()
connection.adapter.virtual_device_name = VIRTUAL_DEVICE_NAME
connection.ipv6_lp = ipv6_leak_protection
connection.killswitch = killswitch
connection.protonvpn_user = protonvpn_user
connection.connection_metadata = connection_metadata
connection.daemon_reconnector = dbus_reconnector
