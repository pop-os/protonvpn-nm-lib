import dbus
from ..logger import logger
from ..services.dbus_get_wrapper import DbusGetWrapper
from ..enums import KillswitchStatusEnum, KillSwitchManagerActionEnum


class MonitorVPNConnectionStart(DbusGetWrapper):
    def __init__(self):
        self.max_attempts = 5
        self.delay = 5000
        self.failed_attempts = 0
        self.loop = None
        self.virtual_device_name = None
        self.user_conf_manager = None
        self.connection_manager = None
        self.reconector_manager = None
        self.ks_manager = None
        self.session = None
        self.bus = None
        self.dbus_response = []

    def start_monitor(self):
        self.vpn_check()

    def setup_monitor(
        self, virtual_device_name, loop,
        ks_manager, user_conf_manager,
        connection_manager, reconector_manager,
        session, dbus_response
    ):
        self.loop = loop
        self.virtual_device_name = virtual_device_name
        self.user_conf_manager = user_conf_manager
        self.connection_manager = connection_manager
        self.reconector_manager = reconector_manager
        self.ks_manager = ks_manager
        self.session = session
        self.dbus_response = dbus_response
        self.bus = dbus.SystemBus()

    def vpn_check(self):
        vpn_interface = self.get_vpn_interface(True)

        if not isinstance(vpn_interface, tuple):
            self.dbus_response["dbus_response"] = "No VPN was found"
            self.loop.quit()

        is_protonvpn, state, conn = self.is_protonvpn_being_prepared()
        if is_protonvpn and state == 1:
            self.vpn_signal_handler(conn)

    def on_vpn_state_changed(self, state, reason):
        logger.info("State: {} - Reason: {}".format(state, reason))

        if state == 5:
            msg = "Successfully connected to ProtonVPN."

            if self.user_conf_manager.killswitch == KillswitchStatusEnum.HARD: # noqa
                self.ks_manager.manage(
                    KillSwitchManagerActionEnum.POST_CONNECTION
                )

            if self.user_conf_manager.killswitch == KillswitchStatusEnum.SOFT: # noqa
                self.ks_manager.manage(KillSwitchManagerActionEnum.SOFT)

            self.session.cache_servers()

            logger.info(msg)
            self.dbus_response["dbus_response"] = msg

            self.reconector_manager.start_daemon_reconnector()
            self.loop.quit()
        elif state in [6, 7]:

            msg = "ProtonVPN connection failed due to "
            if state == 6:
                if reason == 6:
                    msg += "VPN connection time out."
                if reason == 9:
                    msg += "incorrect openvpn credentials."

            if state == 7:
                msg = "ProtonVPN connection has been disconnected. "\
                    "Reason: {}".format(reason)

            logger.error(msg)
            self.dbus_response["dbus_response"] = msg
            self.reconector_manager.stop_daemon_reconnector()
            self.loop.quit()

    def vpn_signal_handler(self, conn):
        """Add signal handler to ProtonVPN connection.

        Args:
            vpn_conn_path (string): path to ProtonVPN connection
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", conn
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.NetworkManager.VPN.Connection"
        )

        try:
            active_conn_props = self.get_active_conn_props(conn)
            logger.info("Adding listener to active {} connection at {}".format(
                active_conn_props["Id"],
                conn)
            )
        except dbus.exceptions.DBusException:
            logger.info(
                "{} is not an active connection.".format(conn)
            )
        else:
            iface.connect_to_signal(
                "VpnStateChanged", self.on_vpn_state_changed
            )
