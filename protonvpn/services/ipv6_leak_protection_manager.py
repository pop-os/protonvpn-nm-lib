import subprocess

import gi

from .. import exceptions
from ..constants import (IPv6_DUMMY_ADDRESS, IPv6_DUMMY_GATEWAY,
                         IPv6_LEAK_PROTECTION_CONN_NAME,
                         IPv6_LEAK_PROTECTION_IFACE_NAME)
from ..logger import logger
from .abstract_interface_manager import AbstractInterfaceManager

gi.require_version("NM", "1.0")
from gi.repository import NM


class IPv6LeakProtectionManager(AbstractInterfaceManager):
    """Manages IPv6 leak protection connection/interfaces."""
    def __init__(
        self,
        iface_name=IPv6_LEAK_PROTECTION_IFACE_NAME,
        conn_name=IPv6_LEAK_PROTECTION_CONN_NAME,
        ipv6_dummy_addrs=IPv6_DUMMY_ADDRESS,
        ipv6_dummy_gateway=IPv6_DUMMY_GATEWAY,
    ):
        self.iface_name = iface_name
        self.conn_name = conn_name
        self.ipv6_dummy_addrs = ipv6_dummy_addrs
        self.ipv6_dummy_gateway = ipv6_dummy_gateway
        self.interface_state_tracker = {
            self.conn_name: {
                "exists": False,
                "is_running": False
            }
        }

    def manage(self, action):
        """Manage IPv6 leak protection.

        Args:
            action (string): either enable or disable
        """
        self.update_connection_status()

        if action == "enable":
            self.add_leak_protection()
        elif action == "disable":
            self.remove_leak_protection()
        else:
            raise exceptions.IPv6LeakProtectionOptionError(
                "Incorrect option for IPv6 leak manager"
            )

    def add_leak_protection(self):
        """Add leak protection connection/interface."""
        self.manage("disable")
        subprocess_command = ""\
            "nmcli c a type dummy ifname {iface} "\
            "con-name {conn} ipv6.method manual "\
            "ipv6.addresses {ipv6_addr} ipv6.gateway {ipv6_gtwy} "\
            "ipv6.route-metric 95".format(
                iface=IPv6_LEAK_PROTECTION_IFACE_NAME,
                conn=IPv6_LEAK_PROTECTION_CONN_NAME,
                ipv6_addr=IPv6_DUMMY_ADDRESS,
                ipv6_gtwy=IPv6_DUMMY_GATEWAY
            ).split(" ")

        if not self.interface_state_tracker[self.conn_name]["exists"]:
            self.run_subprocess(
                exceptions.EnableIPv6LeakProtectionError,
                "Unable to add IPv6 leak protection connection/interface",
                subprocess_command
            )

    def remove_leak_protection(self):
        """Remove leak protection connection/interface."""
        subprocess_command = "nmcli c delete {}".format(
            IPv6_LEAK_PROTECTION_CONN_NAME
        ).split(" ")

        if self.interface_state_tracker[self.conn_name]["exists"]:
            self.run_subprocess(
                exceptions.DisableIPv6LeakProtectionError,
                "Unable to remove IPv6 leak protection connection/interface",
                subprocess_command
            )

    def run_subprocess(self, exception, exception_msg, *args):
        """Run provided input via subprocess.

        Args:
            exception (exceptions.IPv6LeakProtectionError):
                exception based on action
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
            raise exception(exception_msg)

    def update_connection_status(self):
        """Update connection/interface status."""
        client = NM.Client.new(None)
        all_conns = client.get_connections()
        active_conns = client.get_active_connections()

        self.interface_state_tracker[self.conn_name]["exists"] = False
        self.interface_state_tracker[self.conn_name]["is_running"] = False

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
