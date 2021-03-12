from .constants import VIRTUAL_DEVICE_NAME
from .core.dbus import DbusReconnect
from .core.dbus.dbus_monitor_vpn_connection_start import \
    MonitorVPNConnectionStart
from .core.killswitch import KillSwitch

vpn_monitor_connection_start = MonitorVPNConnectionStart()
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

dbus_loop = GLib.MainLoop()


def setup_dbus_vpn_monitor(
    dbus_response, protonvpn_user, session
):
    DBusGMainLoop(set_as_default=True)
    vpn_monitor_connection_start.setup_monitor(
        VIRTUAL_DEVICE_NAME, dbus_loop, DbusReconnect(),
        dbus_response, KillSwitch(), protonvpn_user.settings.killswitch,
        session
    )


def start_dbus_vpn_monitor():
    vpn_monitor_connection_start.start_monitor()
    dbus_loop.run()
