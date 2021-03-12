from .constants import VIRTUAL_DEVICE_NAME

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
# Other
from .core import Country, Utilities, Status

utils = Utilities()

vpn_certificate = VPNCertificate()
server_list = ServerList()
server_filter = ServerFilter()
session = Session()
connection_metadata = ConnectionMetadata()

protonvpn_user = ProtonVPNUser()
protonvpn_user.session = session
protonvpn_user.settings.protonvpn_user = protonvpn_user


country = Country()
server_configurator = ServerConfigurator.init(
    protonvpn_user, server_list
)
connection = Connection()
connection.adapter.virtual_device_name = VIRTUAL_DEVICE_NAME
connection.protonvpn_user = protonvpn_user
connection.connection_metadata = connection_metadata

status = Status()
status.server_list = server_list
status.user_settings = protonvpn_user.settings
