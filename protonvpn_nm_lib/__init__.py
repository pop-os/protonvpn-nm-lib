from .protonvpn_lib import ProtonVPNNMLib
from .dbus_dbus_monitor_vpn_connection_start import MonitorVPNConnectionStart

protonvpn = ProtonVPNNMLib(MonitorVPNConnectionStart())
