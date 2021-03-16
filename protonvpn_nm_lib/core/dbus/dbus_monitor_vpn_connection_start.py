import dbus

from ...enums import (DbusMonitorResponseEnum, DbusVPNConnectionReasonEnum,
                      DbusVPNConnectionStateEnum, KillSwitchActionEnum,
                      KillswitchStatusEnum)
from ...logger import logger
from .dbus_wrapper import DbusWrapper


class MonitorVPNConnectionStart:
    def __init__(self):
        self.max_attempts = 5
        self.delay = 5000
        self.failed_attempts = 0
        self.loop = None
        self.virtual_device_name = None
        self.dbus_reconnector = None
        self.killswitch = None
        self.session = None
        self.bus = None
        self.dbus_response = []
        self.dbus_wrapper = None

    def start_monitor(self):
        self.vpn_check()

    def setup_monitor(
        self, virtual_device_name, loop, dbus_reconnector,
        dbus_response, killswitch, user_killswitch_config,
        session
    ):
        self.loop = loop
        self.virtual_device_name = virtual_device_name
        self.dbus_reconnector = dbus_reconnector
        self.dbus_response = dbus_response
        self.killswitch = killswitch
        self.user_killswitch_config = user_killswitch_config
        self.session = session
        self.bus = dbus.SystemBus()
        self.dbus_wrapper = DbusWrapper(self.bus)

    def vpn_check(self):
        vpn_interface = self.dbus_wrapper.get_vpn_interface()

        if not isinstance(vpn_interface, tuple):
            self.dbus_response[DbusMonitorResponseEnum.RESPONSE] = {
                DbusMonitorResponseEnum.STATE: DbusVPNConnectionStateEnum(999),
                DbusMonitorResponseEnum.MESSAGE: "No VPN was found.",
                DbusMonitorResponseEnum.REASON: DbusVPNConnectionReasonEnum(
                    999
                )
            }
            self.loop.quit()

        (
            is_protonvpn, state, conn
        ) = self.dbus_wrapper.is_protonvpn_being_prepared()
        if is_protonvpn and state == 1:
            self.vpn_signal_handler(conn)

    def on_vpn_state_changed(self, state, reason):
        state = DbusVPNConnectionStateEnum(state)
        reason = DbusVPNConnectionReasonEnum(reason)
        logger.info("State: {} - Reason: {}".format(state, reason))

        if state == DbusVPNConnectionStateEnum.IS_ACTIVE:
            msg = "Successfully connected to ProtonVPN."

            if self.user_killswitch_config == KillswitchStatusEnum.HARD: # noqa
                self.killswitch.manage(
                    KillSwitchActionEnum.POST_CONNECTION
                )

            if self.user_killswitch_config == KillswitchStatusEnum.SOFT: # noqa
                self.killswitch.manage(KillSwitchActionEnum.SOFT)

            self.session.refresh_servers()

            logger.info(msg)
            self.dbus_response[DbusMonitorResponseEnum.RESPONSE] = {
                DbusMonitorResponseEnum.STATE: state,
                DbusMonitorResponseEnum.MESSAGE: msg,
                DbusMonitorResponseEnum.REASON: reason
            }

            self.dbus_reconnector.start_daemon_reconnector()
            self.loop.quit()
        elif state in [
            DbusVPNConnectionStateEnum.FAILED,
            DbusVPNConnectionStateEnum.DISCONNECTED
        ]:

            msg = "ProtonVPN connection failed due to "
            reason = DbusVPNConnectionReasonEnum.UNKNOWN_ERROR
            if state == DbusVPNConnectionStateEnum.FAILED:
                if (
                    reason
                    == DbusVPNConnectionReasonEnum.CONN_ATTEMPT_TO_SERVICE_TIMED_OUT # noqa
                ):
                    msg += "VPN connection time out."
                if (
                    reason
                    == DbusVPNConnectionReasonEnum.SECRETS_WERE_NOT_PROVIDED
                ):
                    msg += "Incorrect openvpn credentials."
            else:
                msg = msg + "unknown reasons."
            if state == DbusVPNConnectionStateEnum.DISCONNECTED:
                msg = "ProtonVPN connection has been disconnected. "\
                    "Reason: {}".format(reason)

            logger.error(msg)
            self.dbus_response[DbusMonitorResponseEnum.RESPONSE] = {
                DbusMonitorResponseEnum.STATE: state,
                DbusMonitorResponseEnum.MESSAGE: msg,
                DbusMonitorResponseEnum.REASON: reason
            }
            self.dbus_reconnector.stop_daemon_reconnector()
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
            active_conn_props = self.dbus_wrapper.get_active_conn_props(conn)
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
