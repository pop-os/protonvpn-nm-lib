import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from protonvpn_nm_lib.constants import VIRTUAL_DEVICE_NAME
from protonvpn_nm_lib.core.environment import ExecutionEnvironment
from protonvpn_nm_lib.daemon.daemon_logger import logger
from protonvpn_nm_lib.enums import (KillSwitchActionEnum,
                                    KillSwitchInterfaceTrackerEnum,
                                    KillswitchStatusEnum,
                                    VPNConnectionReasonEnum,
                                    VPNConnectionStateEnum)

env = ExecutionEnvironment()
connection_metadata = env.connection_metadata
killswitch = env.killswitch
ipv6_leak_protection = env.ipv6leak
settings = env.settings

from protonvpn_nm_lib.core.dbus import DbusWrapper


class ProtonVPNReconnector:
    """Reconnects to VPN if disconnected not by user
        or when connecting to a new network.

    Params:
        virtual_device_name (string): Name of virtual device that will be used
        for ProtonVPNReconnector
        max_attempts (int): Maximum number of attempts ofreconnection VPN
        session on failures
        param delay (int): Miliseconds to wait before reconnecting VPN

    """
    def __init__(self, virtual_device_name, loop, max_attempts=100, delay=5000): # noqa
        logger.info(
            "\n\n------------------------"
            " Initializing Dbus daemon manager "
            "------------------------\n"
        )
        self.virtual_device_name = virtual_device_name
        self.loop = loop
        self.max_attempts = max_attempts
        self.delay = delay
        self.failed_attempts = 0
        self.bus = dbus.SystemBus()
        self.dbus_wrapper = DbusWrapper(self.bus)
        # Auto connect at startup (Listen for StateChanged going forward)
        self.vpn_activator()
        try:
            self.dbus_wrapper.get_network_manager_interface().connect_to_signal( # noqa
                "StateChanged", self.on_network_state_changed
            )
        except Exception as e:
            logger.exception("Exception: {}".format(e))

    def on_network_state_changed(self, state):
        """Network status signal handler.

        Args:
            state (int): connection state (NMState)
        """
        logger.info("Network state changed: {}".format(state))
        if state == 70:
            self.vpn_activator()

    def on_vpn_state_changed(self, state, reason):
        """VPN status signal handler.

        Args:
            state (int): NMVpnConnectionState
            reason (int): NMActiveConnectionStateReason
        """
        state = VPNConnectionStateEnum(state)
        reason = VPNConnectionReasonEnum(reason)
        logger.info(
            "State: {} - ".format(state)
            + "Reason: {}".format(
                reason
            )
        )
        if state == VPNConnectionStateEnum.IS_ACTIVE:
            logger.info(
                "ProtonVPN with virtual device '{}' is running.".format(
                    self.virtual_device_name
                )
            )
            self.failed_attempts = 0

            connection_metadata.save_connect_time()

            try:
                if ipv6_leak_protection.enable_ipv6_leak_protection:
                    ipv6_leak_protection.manage(
                        KillSwitchActionEnum.ENABLE
                    )
            except: # noqa
                pass

            if (
                settings.killswitch
                != KillswitchStatusEnum.DISABLED
            ):
                killswitch.manage(
                    KillSwitchActionEnum.POST_CONNECTION
                )
                logger.info("Running killswitch post-conneciton mode")

        elif (
            state == VPNConnectionStateEnum.DISCONNECTED
            and reason == VPNConnectionReasonEnum.USER_HAS_DISCONNECTED
        ):
            logger.info("ProtonVPN connection was manually disconnected.")
            self.failed_attempts = 0

            try:
                vpn_iface = self.dbus_wrapper.get_vpn_interface()
            except TypeError as e:
                logger.exception(e)

            try:
                vpn_iface.Delete()
            except dbus.exceptions.DBusException as e:
                logger.error(
                    "Unable to remove connection. "
                    + "Exception: {}".format(e)
                )
            except AttributeError:
                pass

            logger.info("ProtonVPN connection has been manually removed.")

            try:
                ipv6_leak_protection.manage(
                    KillSwitchActionEnum.DISABLE
                )
            except: # noqa
                pass

            if (
                settings.killswitch
                != KillswitchStatusEnum.HARD
            ):
                killswitch.delete_all_connections()

            loop.quit()

        elif state in [
            VPNConnectionStateEnum.FAILED,
            VPNConnectionStateEnum.DISCONNECTED
        ]:
            # reconnect if haven't reached max_attempts
            if (
                not self.max_attempts
            ) or (
                self.failed_attempts < self.max_attempts
            ):
                logger.info("Connection failed, attempting to reconnect.")
                self.failed_attempts += 1
                glib_reconnect = True
                GLib.timeout_add(
                    self.delay, self.vpn_activator, glib_reconnect
                )
            else:
                logger.warning(
                    "Connection failed, exceeded {} max attempts.".format(
                        self.max_attempts
                    )
                )
                self.failed_attempts = 0

    def setup_protonvpn_conn(self, active_connection, vpn_interface):
        """Setup and start new ProtonVPN connection.

        Args:
            active_connection (string): path to active connection
            vpn_interface (dbus.Proxy): proxy interface to vpn connection
        """
        new_con = self.dbus_wrapper.activate_connection(
            vpn_interface,
            dbus.ObjectPath("/"),
            active_connection
        )
        self.vpn_signal_handler(new_con)
        logger.info(
            "Starting manually ProtonVPN connection with '{}'.".format(
                self.virtual_device_name
            )
        )

    def manually_start_vpn_conn(self, server_ip, vpn_interface):
        logger.info("User ks setting: {}".format(
            settings.killswitch
        ))
        if (
            settings.killswitch
            != KillswitchStatusEnum.DISABLED
        ):
            try:
                killswitch.manage(
                    KillSwitchActionEnum.PRE_CONNECTION,
                    server_ip=server_ip
                )
            except Exception as e:
                logger.exception(
                    "KS manager reconnect exception: {}".format(e)
                )
                return False
        logger.info("Created routed interface")

        try:
            new_active_connection = self.dbus_wrapper.get_active_connection()
        except (dbus.exceptions.DBusException, Exception) as e:
            logger.exception(e)
            new_active_connection = None

        logger.info(
            "Active conn prior to "
            "setup manual connection: {} {}".format(
                new_active_connection,
                type(new_active_connection)
            )
        )

        if not new_active_connection:
            logger.info("No active connection, retrying reconnect")
            return False
        else:
            logger.info("Setting up manual connection")

            try:
                self.setup_protonvpn_conn(
                    new_active_connection, vpn_interface
                )
            except dbus.exceptions.DBusException as e:
                logger.exception(
                    "Unable to start VPN connection: {}.".format(e)
                )
                return False
            except Exception as e:
                logger.exception(
                    "Unknown reconnector error: {}.".format(e)
                )
                return False

            logger.info(
                "New ProtonVPN connection has been started "
                + "from service."
            )
            return True

    def vpn_activator(self, glib_reconnect=False):
        """Monitor and activate ProtonVPN connections."""
        logger.info(
            "\n\n------- "
            "VPN Activator"
            " -------\n"
            + "Virtual device being monitored: {}; ".format(
                self.virtual_device_name
            ) + "Attempt {}/{} with interval of {} ".format(
                self.failed_attempts, self.max_attempts, self.delay
            ) + "ms;\n"
        )
        vpn_interface = self.dbus_wrapper.get_vpn_interface()

        try:
            active_connection = self.dbus_wrapper.get_active_connection()
        except (dbus.exceptions.DBusException, Exception) as e:
            logger.exception(e)
            active_connection = None

        logger.info("VPN interface: {}".format(vpn_interface))
        logger.info("Active connection: {}".format(active_connection))

        if active_connection is None or vpn_interface is None:
            if not glib_reconnect:
                logger.info("Calling manually on vpn state changed")
                self.on_vpn_state_changed(
                    VPNConnectionStateEnum.FAILED,
                    VPNConnectionReasonEnum.UNKNOWN
                )
            else:
                return True

        (
            is_active_conn_vpn,
            all_vpn_settings
        ) = self.dbus_wrapper.check_active_vpn_conn(
            active_connection
        )

        # Check if primary active connection was started by ProtonVPN client
        if (
            is_active_conn_vpn
        ) and (
            all_vpn_settings["vpn"]["data"]["dev"]
            == self.virtual_device_name
        ):
            logger.info("Primary connection via ProtonVPN.")
            self.vpn_signal_handler(active_connection)
            return False

        server_ip = connection_metadata.get_server_ip()
        logger.info("Reconnecting to server IP \"{}\"".format(server_ip))

        try:
            (
                is_protonvpn, state, conn
            ) = self.dbus_wrapper.is_protonvpn_being_prepared()
        except dbus.exceptions.DBusException as e:
            logger.exception(e)
        else:

            # Check if connection is being prepared
            if is_protonvpn and state == 1:
                logger.info("ProtonVPN connection is being prepared.")
                if (
                    settings.killswitch
                    != KillswitchStatusEnum.DISABLED
                ):
                    killswitch.manage(
                        KillSwitchActionEnum.PRE_CONNECTION,
                        server_ip=server_ip
                    )
                self.vpn_signal_handler(conn)
                return False

        if not self.manually_start_vpn_conn(server_ip, vpn_interface):
            if not glib_reconnect:
                logger.info("Calling manually on vpn state changed")
                self.on_vpn_state_changed(
                    VPNConnectionStateEnum.FAILED,
                    VPNConnectionReasonEnum.UNKNOWN
                )
            else:
                return True

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
        except Exception as e:
            logger.info(
                "Unknown add signal error: {}".format(e)
            )
        else:
            logger.info("Listener added")
            iface.connect_to_signal(
                "VpnStateChanged", self.on_vpn_state_changed
            )


DBusGMainLoop(set_as_default=True)
loop = GLib.MainLoop()
ins = ProtonVPNReconnector(VIRTUAL_DEVICE_NAME, loop)
loop.run()
