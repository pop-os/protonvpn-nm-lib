from ipaddress import ip_network

import dbus
from dbus.mainloop.glib import DBusGMainLoop

from .. import exceptions
from ..constants import (KILLSWITCH_CONN_NAME, KILLSWITCH_INTERFACE_NAME,
                         ROUTED_CONN_NAME, ROUTED_INTERFACE_NAME,
                         IPv4_DUMMY_ADDRESS, IPv4_DUMMY_GATEWAY,
                         IPv6_DUMMY_ADDRESS, IPv6_DUMMY_GATEWAY)
from ..enums import (KillSwitchInterfaceTrackerEnum,
                     KillSwitchManagerActionEnum, KillswitchStatusEnum)
from ..logger import logger
from .abstract_interface_manager import AbstractInterfaceManager
from .dbus_get_wrapper import DbusGetWrapper
from .subprocess_wrapper import subprocess


class KillSwitchManager(AbstractInterfaceManager):
    # Additional loop needs to be create since SystemBus automatically
    # picks the default loop, which is intialized with the CLI.
    # Thus, to refrain SystemBus from using the default loop,
    # one extra loop is needed only to be passed, while it is never used.
    # https://dbus.freedesktop.org/doc/dbus-python/tutorial.html#setting-up-an-event-loop
    dbus_loop = DBusGMainLoop()
    bus = dbus.SystemBus(mainloop=dbus_loop)

    """Manages killswitch connection/interfaces."""
    def __init__(
        self,
        user_conf_manager,
        ks_conn_name=KILLSWITCH_CONN_NAME,
        ks_interface_name=KILLSWITCH_INTERFACE_NAME,
        routed_conn_name=ROUTED_CONN_NAME,
        routed_interface_name=ROUTED_INTERFACE_NAME,
        ipv4_dummy_addrs=IPv4_DUMMY_ADDRESS,
        ipv4_dummy_gateway=IPv4_DUMMY_GATEWAY,
        ipv6_dummy_addrs=IPv6_DUMMY_ADDRESS,
        ipv6_dummy_gateway=IPv6_DUMMY_GATEWAY,
    ):
        self.ks_conn_name = ks_conn_name
        self.ks_interface_name = ks_interface_name
        self.routed_conn_name = routed_conn_name
        self.routed_interface_name = routed_interface_name
        self.ipv4_dummy_addrs = ipv4_dummy_addrs
        self.ipv4_dummy_gateway = ipv4_dummy_gateway
        self.ipv6_dummy_addrs = ipv6_dummy_addrs
        self.ipv6_dummy_gateway = ipv6_dummy_gateway
        self.user_conf_manager = user_conf_manager
        self.dbus_get_wrapper = DbusGetWrapper()
        self.dbus_get_wrapper.bus = self.bus
        self.interface_state_tracker = {
            self.ks_conn_name: {
                KillSwitchInterfaceTrackerEnum.EXISTS: False,
                KillSwitchInterfaceTrackerEnum.IS_RUNNING: False
            },
            self.routed_conn_name: {
                KillSwitchInterfaceTrackerEnum.EXISTS: False,
                KillSwitchInterfaceTrackerEnum.IS_RUNNING: False
            }
        }

        logger.info("Initialized killswitch manager")
        _ = self.check_status_connectivity_check()

    def manage(self, action, server_ip=None):
        """Manage killswitch.

        Args:
            action (string|int): either pre_connection or post_connection
            is_menu (bool): if the action comes from configurations menu,
                if so, then action is int
            server_ip (string): server ip to be connected to
        """
        logger.info(
            "Action({}); Killswitch setting: {}".format(
                action,
                self.user_conf_manager.killswitch
            )
        )
        conn_check = self.connectivity_check()

        if conn_check is not None:
            logger.info("Attempting to disable connectivity check")
            self.disable_connectivity_check(
                conn_check[0], conn_check[1]
            )

        self.update_connection_status()

        actions_dict = {
            KillSwitchManagerActionEnum.PRE_CONNECTION: self.setup_pre_connection_ks, # noqa
            KillSwitchManagerActionEnum.POST_CONNECTION: self.setup_post_connection_ks, # noqa
            KillSwitchManagerActionEnum.SOFT: self.setup_soft_connection,
            KillSwitchManagerActionEnum.DISABLE: self.delete_all_connections

        }[action](server_ip)

    def update_from_user_configuration_menu(self, action):
        logger.info(
            "Action({}); Killswitch setting: {}".format(
                action,
                self.user_conf_manager.killswitch
            )
        )
        if action == KillswitchStatusEnum.HARD:
            self.create_killswitch_connection()
        elif action in [
            KillswitchStatusEnum.SOFT, KillswitchStatusEnum.DISABLED
        ]:
            self.delete_all_connections()
        else:
            raise exceptions.KillswitchError(
                "Incorrect option for killswitch manager"
            )

    def setup_pre_connection_ks(self, server_ip, pre_attempts=0):
        """Assure pre-connection Kill Switch is setup correctly.

        Args:
            server_ip (list | string): ProtonVPN server IP
            pre_attempts (int): number of setup attempts
        """
        if pre_attempts >= 5:
            raise exceptions.KillswitchError(
                "Unable to setup pre-connection ks. "
                "Exceeded maximum attempts."
            )

        # happy path
        if (
            self.interface_state_tracker[self.ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
            and not self.interface_state_tracker[self.routed_conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]
        ):
            self.create_routed_connection(server_ip)
            self.deactivate_connection(self.ks_conn_name)
            return

        # check for routed ks and remove if present/running
        if (
            self.interface_state_tracker[self.routed_conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]
            or self.interface_state_tracker[self.routed_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            self.delete_connection(self.routed_conn_name)

        # check if ks exists. Start it if it does
        if (
            self.interface_state_tracker[
                self.ks_conn_name
            ][KillSwitchInterfaceTrackerEnum.EXISTS]
        ):
            self.activate_connection(self.ks_conn_name)

        # check if ks does not exist, if not then create and start it
        if (
            not self.interface_state_tracker[
                self.ks_conn_name
            ][KillSwitchInterfaceTrackerEnum.EXISTS]
        ):
            self.create_killswitch_connection()

        pre_attempts += 1
        self.update_connection_status()
        self.setup_pre_connection_ks(server_ip, pre_attempts=pre_attempts)

    def setup_post_connection_ks(
        self, _, post_attempts=0, activating_soft_connection=False
    ):
        """Assure post-connection Kill Switch is setup correctly.

        Args:
            post_attempts (int): number of setup attempts
        """
        if post_attempts >= 5:
            raise exceptions.KillswitchError(
                "Unable to setup post-connection ks. "
                "Exceeded maximum attempts."
            )

        # happy path
        if (
            not self.interface_state_tracker[self.ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
            and self.interface_state_tracker[self.routed_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            self.activate_connection(self.ks_conn_name)
            self.delete_connection(self.routed_conn_name)
            return
        elif (
            activating_soft_connection
            and (
                not self.interface_state_tracker[self.routed_conn_name][KillSwitchInterfaceTrackerEnum.IS_RUNNING] # noqa
                or not self.interface_state_tracker[self.routed_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] # noqa
            )
        ):
            self.activate_connection(self.ks_conn_name)
            return

        # check for ks and disable it if is running
        if (
            self.interface_state_tracker[self.ks_conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ):
            self.deactivate_connection(self.ks_conn_name)

        # check if routed ks exists, if so then activate it
        # else raise exception
        if (
            self.interface_state_tracker[self.routed_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] # noqa
        ):
            self.activate_connection(self.routed_conn_name)
        else:
            raise Exception("Routed connection does not exist")

        post_attempts += 1
        self.update_connection_status()
        self.setup_post_connection_ks(
            _, post_attempts=post_attempts,
            activating_soft_connection=activating_soft_connection
        )

    def setup_soft_connection(self, _):
        """Setup Kill Switch for --on setting."""
        self.create_killswitch_connection()
        self.setup_post_connection_ks(None, activating_soft_connection=True)

    def create_killswitch_connection(self):
        """Create killswitch connection/interface."""
        subprocess_command = [
            "nmcli", "c", "a", "type", "dummy",
            "ifname", self.ks_interface_name,
            "con-name", self.ks_conn_name,
            "ipv4.method", "manual",
            "ipv4.addresses", self.ipv4_dummy_addrs,
            "ipv4.gateway", self.ipv4_dummy_gateway,
            "ipv6.method", "manual",
            "ipv6.addresses", self.ipv6_dummy_addrs,
            "ipv6.gateway", self.ipv6_dummy_gateway,
            "ipv4.route-metric", "98",
            "ipv6.route-metric", "98"
        ]

        self.create_connection(
            self.ks_conn_name,
            "Unable to activate {}".format(self.ks_conn_name),
            subprocess_command, exceptions.CreateBlockingKillswitchError
        )

    def create_routed_connection(self, server_ip, try_route_addrs=False):
        """Create routed connection/interface.

        Args:
            server_ip (list(string)): the IP of the server to be connected
        """
        if isinstance(server_ip, list):
            server_ip = server_ip.pop()

        subnet_list = list(ip_network('0.0.0.0/0').address_exclude(
            ip_network(server_ip)
        ))

        route_data = [str(ipv4) for ipv4 in subnet_list]
        route_data_str = ",".join(route_data)

        subprocess_command = [
            "nmcli", "c", "a", "type", "dummy",
            "ifname", self.routed_interface_name,
            "con-name", self.routed_conn_name,
            "ipv4.method", "manual",
            "ipv4.addresses", self.ipv4_dummy_addrs,
            "ipv6.method", "manual",
            "ipv6.addresses", self.ipv6_dummy_addrs,
            "ipv6.gateway", self.ipv6_dummy_gateway,
            "ipv4.route-metric", "97",
            "ipv6.route-metric", "97",
            "ipv4.routes", route_data_str
        ]

        if try_route_addrs:
            subprocess_command = [
                "nmcli", "c", "a", "type", "dummy",
                "ifname", self.routed_interface_name,
                "con-name", self.routed_conn_name,
                "ipv4.method", "manual",
                "ipv4.addresses", route_data_str,
                "ipv6.method", "manual",
                "ipv6.addresses", self.ipv6_dummy_addrs,
                "ipv6.gateway", self.ipv6_dummy_gateway,
                "ipv4.route-metric", "97",
                "ipv6.route-metric", "97"
            ]

        logger.info(subprocess_command)
        exception_msg = "Unable to activate {}".format(self.routed_conn_name)

        try:
            self.create_connection(
                self.routed_conn_name, exception_msg,
                subprocess_command, exceptions.CreateRoutedKillswitchError
            )
        except exceptions.CreateRoutedKillswitchError as e:
            if e.additional_context.returncode == 2 and not try_route_addrs:
                return self.create_routed_connection(server_ip, True)
            else:
                raise exceptions.CreateRoutedKillswitchError(exception_msg)

    def create_connection(
        self, conn_name, exception_msg,
        subprocess_command, exception
    ):
        self.update_connection_status()
        if not self.interface_state_tracker[conn_name][
            KillSwitchInterfaceTrackerEnum.EXISTS
        ]:
            self.run_subprocess(
                exception,
                exception_msg,
                subprocess_command
            )

    def activate_connection(self, conn_name):
        """Activate a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        self.update_connection_status()
        conn_dict = self.dbus_get_wrapper.search_for_connection( # noqa
            conn_name,
            return_device_path=True,
            return_settings_path=True
        )
        if (
            self.interface_state_tracker[conn_name][
                KillSwitchInterfaceTrackerEnum.EXISTS
            ]
        ) and (
            not self.interface_state_tracker[conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ]
        ) and conn_dict:
            device_path = str(conn_dict.get("device_path"))
            settings_path = str(conn_dict.get("settings_path"))

            try:
                active_conn = self.dbus_get_wrapper.activate_connection(
                    settings_path, device_path
                )
            except dbus.exceptions.DBusException as e:
                logger.exception(e)
                raise exceptions.ActivateKillswitchError(
                    "Unable to activate {}".format(conn_name)
                )
            else:
                if active_conn:
                    return
                logger.error(
                    "Dbus returned empty, unable to activate connection"
                )
                raise exceptions.ActivateKillswitchError(
                    "Unable to activate {}".format(conn_name)
                )

    def deactivate_connection(self, conn_name):
        """Deactivate a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        self.update_connection_status()
        active_conn_dict = self.dbus_get_wrapper.search_for_connection( # noqa
            conn_name, is_active=True,
            return_active_conn_path=True
        )
        if (
            self.interface_state_tracker[conn_name][
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ] and active_conn_dict
        ):
            active_conn_path = str(active_conn_dict.get("active_conn_path"))
            try:
                self.dbus_get_wrapper.disconnect_connection(
                    active_conn_path
                )
            except dbus.exceptions.DBusException as e:
                logger.exception(e)
                raise exceptions.DectivateKillswitchError(
                    "Unable to deactivate {}".format(conn_name)
                )

    def delete_connection(self, conn_name):
        """Delete a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        subprocess_command = ""\
            "nmcli c delete {}".format(conn_name).split(" ")

        self.update_connection_status()
        if self.interface_state_tracker[conn_name][KillSwitchInterfaceTrackerEnum.EXISTS]: # noqa
            self.run_subprocess(
                exceptions.DeleteKillswitchError,
                "Unable to delete {}".format(conn_name),
                subprocess_command
            )

    def deactivate_all_connections(self):
        """Deactivate all connections."""
        self.deactivate_connection(self.ks_conn_name)
        self.deactivate_connection(self.routed_conn_name)

    def delete_all_connections(self, _=None):
        """Delete all connections."""
        self.delete_connection(self.ks_conn_name)
        self.delete_connection(self.routed_conn_name)

    def update_connection_status(self):
        """Update connection/interface status."""
        all_conns = self.dbus_get_wrapper.get_all_conns()
        active_conns = self.dbus_get_wrapper.get_all_active_conns()
        self.interface_state_tracker[self.ks_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] = False # noqa
        self.interface_state_tracker[self.routed_conn_name][KillSwitchInterfaceTrackerEnum.EXISTS] = False  # noqa
        self.interface_state_tracker[self.ks_conn_name][KillSwitchInterfaceTrackerEnum.IS_RUNNING] = False # noqa
        self.interface_state_tracker[self.routed_conn_name][KillSwitchInterfaceTrackerEnum.IS_RUNNING] = False  # noqa

        for conn in all_conns:
            try:
                conn_name = str(self.dbus_get_wrapper.get_all_conn_settings(
                    conn
                )["connection"]["id"])
            except dbus.exceptions.DBusException:
                conn_name = "None"

            if conn_name in self.interface_state_tracker:
                self.interface_state_tracker[conn_name][
                    KillSwitchInterfaceTrackerEnum.EXISTS
                ] = True

        for active_conn in active_conns:
            try:
                conn_name = str(self.dbus_get_wrapper.get_active_conn_props(
                    active_conn
                )["Id"])
            except dbus.exceptions.DBusException:
                conn_name = "None"

            if conn_name in self.interface_state_tracker:
                self.interface_state_tracker[conn_name][
                    KillSwitchInterfaceTrackerEnum.IS_RUNNING
                ] = True

        logger.info("Tracker info: {}".format(self.interface_state_tracker))

    def run_subprocess(self, exception, exception_msg, *args):
        """Run provided input via subprocess.

        Args:
            exception (exceptions.KillswitchError): exception based on action
            exception_msg (string): exception message
            *args (list): arguments to be passed to subprocess
        """
        subprocess_outpout = subprocess.run(
            *args, stderr=subprocess.PIPE, stdout=subprocess.PIPE
        )

        if (
            subprocess_outpout.returncode != 0
            and subprocess_outpout.returncode != 10
        ):
            logger.error(
                "Interface state tracker: {}".format(
                    self.interface_state_tracker
                )
            )
            logger.error(
                "[!] {}: {}. Raising exception.".format(
                    exception,
                    subprocess_outpout
                )
            )
            raise exception(
                exception_msg,
                subprocess_outpout
            )

    def connectivity_check(self):
        (
            is_conn_check_available,
            is_conn_check_enabled,
        ) = self.check_status_connectivity_check()

        if not is_conn_check_enabled:
            return None

        if not is_conn_check_available:
            logger.error(
                "[!] AvailableConnectivityCheckError: "
                + "Unable to change connectivity check for killswitch."
                + "Raising exception."
            )
            raise exceptions.AvailableConnectivityCheckError(
                "Unable to change connectivity check for killswitch"
            )

        return is_conn_check_available, is_conn_check_enabled

    def check_status_connectivity_check(self):
        """Check status of NM connectivity check."""
        nm_props = self.dbus_get_wrapper.get_network_manager_properties()
        is_conn_check_available = nm_props["ConnectivityCheckAvailable"]
        is_conn_check_enabled = nm_props["ConnectivityCheckEnabled"]

        logger.info(
            "Conn check available ({}) - Conn check enabled ({})".format(
                is_conn_check_available,
                is_conn_check_enabled
            )
        )

        return is_conn_check_available, is_conn_check_enabled

    def disable_connectivity_check(
        self, is_conn_check_available, is_conn_check_enabled
    ):
        """Disable NetworkManager connectivity check."""
        if is_conn_check_enabled:
            logger.info("Disabling connectivity check")
            nm = self.dbus_get_wrapper.get_network_manager_properties_interface() # noqa
            nm.Set(
                "org.freedesktop.NetworkManager",
                "ConnectivityCheckEnabled",
                False
            )
            nm_props = self.dbus_get_wrapper.get_network_manager_properties()
            if nm_props["ConnectivityCheckEnabled"]:
                logger.error(
                    "[!] DisableConnectivityCheckError: "
                    + "Can not disable connectivity check for killswitch."
                    + "Raising exception."
                )
                raise exceptions.DisableConnectivityCheckError(
                    "Can not disable connectivity check for killswitch"
                )

            logger.info("Check connectivity has been 'disabled'")
