import subprocess
from ipaddress import ip_network

import gi

from ..constants import (KILLSWITCH_CONN_NAME, KILLSWITCH_INTERFACE_NAME,
                         ROUTED_CONN_NAME, ROUTED_INTERFACE_NAME,
                         IPv4_DUMMY_ADDRESS, IPv4_DUMMY_GATEWAY,
                         IPv6_DUMMY_ADDRESS, IPv6_DUMMY_GATEWAY)
from ..enums import KillswitchStatusEnum
from ..logger import logger
from .. import exceptions
from .abstract_interface_manager import AbstractInterfaceManager

gi.require_version("NM", "1.0")
from gi.repository import NM, GLib # noqa


class KillSwitchManager(AbstractInterfaceManager):
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
        self.interface_state_tracker = {
            self.ks_conn_name: {
                "exists": False,
                "is_running": False
            },
            self.routed_conn_name: {
                "exists": False,
                "is_running": False
            }
        }

        logger.info("Initialized killswitch manager")
        _ = self.check_status_connectivity_check()

    def manage(self, action, is_menu=False, server_ip=None):
        """Manage killswitch.

        Args:
            action (string|int): either pre_connection or post_connection
            is_menu (bool): if the action comes from configurations menu,
                if so, then action is int
            server_ip (string): server ip to be connected to
        """
        logger.info(
            "Action({}) -> is_menu({}); Killswitch setting: {}".format(
                action,
                is_menu,
                self.user_conf_manager.killswitch
            )
        )

        (
            client,
            conn_check_available,
            conn_check_enabled
        ) = self.connectivity_check()

        if client is not None:
            logger.info("client is not None, will attempt to disable")
            self.disable_connectivity_check(
                client, conn_check_available, conn_check_enabled
            )

        self.update_connection_status()

        if is_menu:
            if int(action) == KillswitchStatusEnum.HARD:
                self.create_killswitch_connection()
            elif int(action) in [
                KillswitchStatusEnum.SOFT, KillswitchStatusEnum.DISABLED
            ]:
                self.delete_all_connections()
            else:
                raise exceptions.KillswitchError(
                    "Incorrect option for killswitch manager"
                )

            return

        if (
            action == "pre_connection"
        ) and (
            self.interface_state_tracker[self.ks_conn_name]["is_running"]
            and not self.interface_state_tracker[self.routed_conn_name]["exists"] # noqa
        ):
            self.create_routed_connection(server_ip)
            self.deactivate_connection(self.ks_conn_name)
        elif (
            action == "post_connection"
        ) and (
            not self.interface_state_tracker[self.ks_conn_name]["is_running"]
            and self.interface_state_tracker[self.routed_conn_name]["is_running"] # noqa
        ):
            self.activate_connection(self.ks_conn_name)
            self.delete_connection(self.routed_conn_name)
        elif action == "soft_connection":
            self.create_killswitch_connection()
            self.manage("post_connection")
        elif action == "disable":
            self.delete_all_connections()

    def create_killswitch_connection(self):
        """Create killswitch connection/interface."""
        subprocess_command = ""\
            "nmcli c a type dummy ifname {interface_name} "\
            "con-name {conn_name} ipv4.method manual "\
            "ipv4.addresses {ipv4_addrs} ipv4.gateway {ipv4_gateway} "\
            "ipv6.method manual ipv6.addresses {ipv6_addrs} "\
            "ipv6.gateway {ipv6_gateway} "\
            "ipv4.route-metric 98 ipv6.route-metric 98".format(
                conn_name=self.ks_conn_name,
                interface_name=self.ks_interface_name,
                ipv4_addrs=self.ipv4_dummy_addrs,
                ipv4_gateway=self.ipv4_dummy_gateway,
                ipv6_addrs=self.ipv6_dummy_addrs,
                ipv6_gateway=self.ipv6_dummy_gateway,
            ).split(" ")

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

        subprocess_command = ""\
            "nmcli c a type dummy ifname {interface_name} "\
            "con-name {conn_name} ipv4.method manual "\
            "ipv4.addresses {ipv4_addrs} "\
            "ipv6.method manual ipv6.addresses {ipv6_addrs} "\
            "ipv6.gateway {ipv6_gateway} "\
            "ipv4.route-metric 97 ipv6.route-metric 97 "\
            "ipv4.routes {routes}".format(
                conn_name=self.routed_conn_name,
                interface_name=self.routed_interface_name,
                ipv4_addrs=self.ipv4_dummy_addrs,
                ipv6_addrs=self.ipv6_dummy_addrs,
                ipv6_gateway=self.ipv6_dummy_gateway,
                routes=route_data_str
            ).split(" ")

        if try_route_addrs:
            subprocess_command = ""\
                "nmcli c a type dummy ifname {interface_name} "\
                "con-name {conn_name} ipv4.method manual "\
                "ipv4.addresses {ipv4_addrs} "\
                "ipv6.method manual ipv6.addresses {ipv6_addrs} "\
                "ipv6.gateway {ipv6_gateway} "\
                "ipv4.route-metric 97 ipv6.route-metric 97".format(
                    conn_name=self.routed_conn_name,
                    interface_name=self.routed_interface_name,
                    ipv4_addrs=route_data_str,
                    ipv6_addrs=self.ipv6_dummy_addrs,
                    ipv6_gateway=self.ipv6_dummy_gateway,
                ).split(" ")

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
        if not self.interface_state_tracker[conn_name]["exists"]:
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
        subprocess_command = ""\
            "nmcli c up {}".format(conn_name).split(" ")

        self.update_connection_status()
        if (
            self.interface_state_tracker[conn_name]["exists"]
        ) and (
            not self.interface_state_tracker[conn_name]["is_running"]
        ):
            self.run_subprocess(
                exceptions.ActivateKillswitchError,
                "Unable to activate {}".format(conn_name),
                subprocess_command
            )

    def deactivate_connection(self, conn_name):
        """Deactivate a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        subprocess_command = ""\
            "nmcli c down {}".format(conn_name).split(" ")

        self.update_connection_status()
        if self.interface_state_tracker[conn_name]["is_running"]: # noqa
            self.run_subprocess(
                exceptions.DectivateKillswitchError,
                "Unable to deactivate {}".format(conn_name),
                subprocess_command
            )

    def delete_connection(self, conn_name):
        """Delete a connection based on connection name.

        Args:
            conn_name (string): connection name (uid)
        """
        subprocess_command = ""\
            "nmcli c delete {}".format(conn_name).split(" ")

        self.update_connection_status()
        if self.interface_state_tracker[conn_name]["exists"]: # noqa
            self.run_subprocess(
                exceptions.DeleteKillswitchError,
                "Unable to delete {}".format(conn_name),
                subprocess_command
            )

    def deactivate_all_connections(self):
        """Deactivate all connections."""
        self.deactivate_connection(self.ks_conn_name)
        self.deactivate_connection(self.routed_conn_name)

    def delete_all_connections(self):
        """Delete all connections."""
        self.delete_connection(self.ks_conn_name)
        self.delete_connection(self.routed_conn_name)

    def update_connection_status(self):
        """Update connection/interface status."""
        client = NM.Client.new(None)
        all_conns = client.get_connections()
        active_conns = client.get_active_connections()

        self.interface_state_tracker[self.ks_conn_name]["exists"] = False # noqa
        self.interface_state_tracker[self.routed_conn_name]["exists"] = False  # noqa
        self.interface_state_tracker[self.ks_conn_name]["is_running"] = False # noqa
        self.interface_state_tracker[self.routed_conn_name]["is_running"] = False  # noqa

        for conn in all_conns:
            try:
                self.interface_state_tracker[conn.get_id()]
            except KeyError:
                pass
            else:
                self.interface_state_tracker[conn.get_id()]["exists"] = True

        for active_conn in active_conns:
            try:
                self.interface_state_tracker[active_conn.get_id()]
            except KeyError:
                pass
            else:
                self.interface_state_tracker[active_conn.get_id()]["is_running"] = True # noqa

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
            client
        ) = self.check_status_connectivity_check()

        if not is_conn_check_enabled:
            return (None, None, None)

        if not is_conn_check_available:
            logger.error(
                "[!] AvailableConnectivityCheckError: "
                + "Unable to change connectivity check for killswitch."
                + "Raising exception."
            )
            raise exceptions.AvailableConnectivityCheckError(
                "Unable to change connectivity check for killswitch"
            )

        return client, is_conn_check_available, is_conn_check_enabled

    def check_status_connectivity_check(self):
        """Check status of NM connectivity check."""
        client = NM.Client.new(None)
        is_conn_check_available = client.connectivity_check_get_available()
        is_conn_check_enabled = client.connectivity_check_get_enabled()

        logger.info(
            "Conn check available ({}) - Conn check enabled ({})".format(
                is_conn_check_available,
                is_conn_check_enabled
            )
        )

        return is_conn_check_available, is_conn_check_enabled, client

    def disable_connectivity_check(
        self, client, is_conn_check_available, is_conn_check_enabled
    ):
        """Disable NetworkManager connectivity check."""
        if is_conn_check_enabled:
            logger.info("Disabling connectivity check")
            # client.dbus_set_property(
            #     "/org/freedesktop/NetworkManager",
            #     "org.freedesktop.NetworkManager",
            #     "ConnectivityCheckEnabled",
            #     GLib.Variant.new_boolean(False),
            #     -1, None, None, None
            # )
            client.props.connectivity_check_enabled = False
            client = NM.Client.new(None)
            if client.props.connectivity_check_enabled:
                logger.error(
                    "[!] DisableConnectivityCheckError: "
                    + "Can not disable connectivity check for killswitch."
                    + "Raising exception."
                )
                raise exceptions.DisableConnectivityCheckError(
                    "Can not disable connectivity check for killswitch"
                )

            logger.info("Check connectivity has been 'disabled'")
