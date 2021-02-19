from .services.dbus_dbus_monitor_vpn_connection_start import \
    MonitorVPNConnectionStart
from .protonvpn_lib import ProtonVPNNMLib

protonvpn = ProtonVPNNMLib(MonitorVPNConnectionStart())
