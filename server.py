import time
import gi
gi.require_version("NM", "1.0")
from gi.repository import NM, Gio
from lib.services.connection_manager import ConnectionManager
from lib.services.plugin_manager import PluginManager
from lib import exceptions

cm = ConnectionManager(PluginManager())
last_conn_state = False


def yield_active_connections(provided_client):
    active_conns = provided_client.get_active_connections()
    for active_conn in active_conns:
        yield active_conn


while True:
    client = NM.Client.new(Gio.Cancellable.new())
    general_conn_state = client.get_state().value_name
    if general_conn_state != "NM_STATE_CONNECTED_GLOBAL":
        # print("No internet connection: ", general_conn_state)
        last_conn_state = general_conn_state
        continue
    else:
        if last_conn_state == "NM_STATE_CONNECTED_SITE":
            yielded_active_conns = yield_active_connections(client)
            vpn = [
                vpn_conn
                for vpn_conn in
                yielded_active_conns if isinstance(vpn_conn, NM.VpnConnection)
            ]
            try:
                vpn[0].get_vpn_state()
            except IndexError:
                try:
                    cm.start_connection()
                except exceptions.CustomBaseException as e:
                    print(e)
    # time.sleep(0.5)








# print("Overall network state: ", client.get_state())
# print(client.networking_get_enabled())
# print(client.wireless_get_enabled())
# print(client.wireless_hardware_get_enabled())
# print("Props: ", client.props.active_connections[0].get_id())
# print("Props: ", client.props.can_modify)
# print("Props: ", client.props.connectivity)
# print("Props: ", client.props.connectivity_check_available)
# print("get_id: ", client.props.primary_connection.get_id())
# print("state: ", client.props.state)
# print("get_domains: ", client.props.dns_configuration[0].get_domains())
# print("get_interface: ", client.props.dns_configuration[0].get_interface())
# print("get_nameservers: ", client.props.dns_configuration[0].get_nameservers())
# print("get_priority: ", client.props.dns_configuration[0].get_priority())
# print("get_vpn: ", client.props.dns_configuration[0].get_vpn())
