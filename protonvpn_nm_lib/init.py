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
connection.reconnector = dbus_reconnector


def parse_user_input(
    connection_type,
    connection_type_extra_arg=None,
    protocol=None
):
    if connection_type == ConnectionTypeEnum.COUNTRY:
        country.ensure_country_exists(connection_type_extra_arg)
    if connection_type == ConnectionTypeEnum.SERVERNAME:
        utils.ensure_servername_is_valid(
            connection_type_extra_arg
        )

    connection_type = connection_type
    connection_type_extra_arg = connection_type_extra_arg

    if connection_type not in [
        ConnectionTypeEnum.SERVERNAME, ConnectionTypeEnum.COUNTRY
    ]:
        connection_type_extra_arg = connection_type

    if not utils.is_protocol_valid(protocol):
        protocol = ProtocolEnum(
            protonvpn_user.settings.protocol
        )
    else:
        protocol = ProtocolEnum(protocol)

    return connection_type, connection_type_extra_arg, protocol


def post_setup_connection_save_metadata(servername, protocol, physical_server):
    connection_metadata.save_servername(servername)
    connection_metadata.save_protocol(protocol)
    connection_metadata.save_display_server_ip(physical_server.exit_ip)
    connection_metadata.save_server_ip(physical_server.entry_ip)

# def setup_dbus_vpn_monitor(self, dbus_response):
#     DBusGMainLoop(set_as_default=True)
#     self.dbus_loop = GLib.MainLoop()
#     self.__vpn_monitor_connection_start.setup_monitor(
#         VIRTUAL_DEVICE_NAME, self.dbus_loop,
#         self.__ks_manager, self.__user_conf_manager,
#         self.__connection_manager, self.__reconector_manager,
#         self.__user_session, dbus_response
#     )

# def start_dbus_vpn_monitor(self):
#     self.__vpn_monitor_connection_start.start_monitor()
#     self.dbus_loop.run()