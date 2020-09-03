"""
Copyright 2011 Domen Kozar. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following
conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY DOMEN KOZAR ''AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL DOMEN KOZAR OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation
are those of the authors and should not be interpreted as representing
official policies, either expressed or implied, of DOMEN KOZAR.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from lib.constants import LOGFILE, PROTON_XDG_CACHE_HOME_LOGS
from lib.exceptions import (ConnectionNotFound, StartConnectionFinishError,
                            StopConnectionFinishError)
from lib.services.connection_manager import ConnectionManager

if not os.path.isdir(PROTON_XDG_CACHE_HOME_LOGS):
    os.mkdir(PROTON_XDG_CACHE_HOME_LOGS)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    filemode="a",
)

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s" # noqa
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(FORMATTER)


file_handler = RotatingFileHandler(
    LOGFILE,
    maxBytes=3145728,
    backupCount=1
)
file_handler.setFormatter(FORMATTER)
logger.addHandler(file_handler)


class ProtonVPNReconnector(object):
    """Reconnects to VPN if disconnected not by user
    or when connecting to a new network.

    Params:
        vpn_name (string): Name of VPN connection that will be used
        for ProtonVPNReconnector
        max_attempts (int): Maximum number of attempts ofreconnection VPN
        session on failures
        param delay (int): Miliseconds to wait before reconnecting VPN

    """
    def __init__(self, vpn_name, loop, max_attempts=5, delay=5000):
        self.vpn_name = vpn_name
        self.loop = loop
        self.max_attempts = max_attempts
        self.delay = delay
        self.failed_attempts = 0
        self.bus = dbus.SystemBus()
        # Auto connect at startup (Listen for StateChanged going forward)
        self.vpn_monitor()
        self.get_network_manager().connect_to_signal(
            "StateChanged", self.on_network_state_changed
        )
        logger.info(
            "____Monitoring connection "
            + "for {}, ".format(vpn_name)
            + "reattempting up to {} times with {} ".format(
                max_attempts, delay
            )
            + "ms between retries____\n\n"
        )

    def on_network_state_changed(self, state):
        """Network status handler and VPN activator."""
        logger.debug("Network state changed: {}".format(state))
        if state == 70:
            self.vpn_monitor()

    def on_vpn_state_changed(self, state, reason):
        """VPN status handler and reconnector."""
        # vpn connected or user disconnected manually?
        # reason: enum NMActiveConnectionStateReason
        # state: enum NMVpnConnectionState
        logger.info(
            "State(NMVpnConnectionState): {} - ".format(state)
            + "Reason(NMActiveConnectionStateReason): {}".format(
                reason
            )
        )
        if state == 5 or (state == 7 and reason == 2):
            self.failed_attempts = 0
            if state == 5:
                logger.info("VPN {} connected".format(self.vpn_name))
            else:
                logger.info("[!] User disconnected manually")
                try:
                    cm = ConnectionManager()
                    cm.remove_connection()
                except (
                    ConnectionNotFound, StopConnectionFinishError,
                    StartConnectionFinishError
                ) as e:
                    logger.info(
                        "Unable to remove connection via daemon."
                        + "Exception: {}".format(e)
                    )
                finally:
                    loop.quit()
            return
        # connection failed or unknown?
        elif state in [6, 7]:
            # reconnect if we haven't reached max_attempts
            if (
                not self.max_attempts
            ) or (
                self.failed_attempts < self.max_attempts
            ):
                logger.info("[!] Connection failed, attempting to reconnect")
                self.failed_attempts += 1
                GLib.timeout_add(self.delay, self.vpn_monitor)
            else:
                logger.info(
                    "[!] Connection failed, exceeded {} max attempts.".format(
                        self.max_attempts
                    )
                )
                self.failed_attempts = 0

    def get_network_manager(self):
        """Gets the network manager dbus interface."""
        logger.debug("Getting NetworkManager DBUS interface")
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        return dbus.Interface(proxy, "org.freedesktop.NetworkManager")

    def get_vpn_interface(self, virtual_device_name, return_properties=False):
        """Gets VPN connection interface with the specified virtual device name.

        Args:
            virtual_device_name (string): virtual device name (proton0, etc)
        Returns:
            dbus.proxies.Interface
        """
        logger.debug(
            "Searching after {} VPN DBUS interface", virtual_device_name
        )
        connections = self.get_all_conns()
        for connection in connections:
            all_settings, iface = self.get_all_conn_settings(
                connection, return_iface=True
            )
            # all_settings[
            #   connection dbus.Dictionary
            #   vpn dbus.Dictionary
            #   ipv4 dbus.Dictionary
            #   ipv6 dbus.Dictionary
            #   proxy dbus.Dictionary
            # ]
            if (
                all_settings["connection"]["type"] == "vpn"
            ) and (
                all_settings["vpn"]["data"]["dev"] == virtual_device_name
            ):
                logger.debug(
                    "Detected interface for virtual device "
                    + "'{}'.".format(virtual_device_name)
                )
                if return_properties:
                    return all_settings
                return iface

        logger.error(
            "[!] Could not find interface belonging to '{}'.".format(
                virtual_device_name
            )
        )
        return None

    def get_active_connection(self):
        """Gets the dbus interface of an active
        network connection with a default route(s).

        Returns:
            dbus.ObjectPath to active connection with default route(s).
        """
        logger.debug("Getting active network connection")
        active_connections = self.get_all_active_conns()
        if len(active_connections) == 0:
            logger.info("No active connection were found.")
            return None

        for active_conn in active_connections:
            active_conn_props = self.get_active_conn_props(active_conn)
            if (
                active_conn_props["Default"]
            ) or (
                active_conn_props["Default"] and active_conn_props["Default6"]
            ):
                logger.info(
                    "Detected ({}) active ".format(
                        active_conn_props["Id"]
                    )
                    + "connection that has default route(s) "
                    + "IPv4: {} / IPv6: {}".format(
                        active_conn_props["Default"],
                        active_conn_props["Default6"]
                    )
                )
                return active_conn

    def get_all_conn_settings(self, active_conn, return_iface=False):
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", active_conn
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.NetworkManager.Settings.Connection"
        )
        if return_iface:
            return (iface.GetSettings(), iface)

        return iface.GetSettings()

    def get_active_conn_props(self, active_conn, return_iface=False):
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", active_conn
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.DBus.Properties"
        )
        if return_iface:
            return (
                iface.GetAll(
                    "org.freedesktop.NetworkManager.Connection.Active"
                ),
                iface
            )
        return iface.GetAll(
            "org.freedesktop.NetworkManager.Connection.Active"
        )

    def get_all_conns(self):
        """Get all existing connections

        Returns:
            list: contains path to connection(object) settings
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager/Settings"
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.NetworkManager.Settings"
        )
        return iface.ListConnections()

    def get_all_active_conns(self):
        """Get all active connections

        Returns:
            list: contains path to active connection(object)
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        iface = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")

        return iface.Get(
            "org.freedesktop.NetworkManager", "ActiveConnections"
        )

    def vpn_monitor(self):
        """VPN monitor."""
        logger.info("Starting {} VPN monitor".format(self.vpn_name))
        vpn_interface = self.get_vpn_interface(self.vpn_name)
        active_con = self.get_active_connection()
        if active_con is None:
            return

        if vpn_interface and active_con:
            try:
                new_con = self.get_network_manager().ActivateConnection(
                    vpn_interface,
                    dbus.ObjectPath("/"),
                    active_con,
                )
                self.vpn_signal_handler(new_con)
                logger.info(
                    "VPN {} should soon be active".format(self.vpn_name)
                )
            except dbus.exceptions.DBusException as e:
                if "ConnectionAlreadyActive" in str(e):
                    logger.info(
                        "Detected active connection with virtual "
                        + "device ({}) ".format(
                            self.vpn_name
                        )
                        + "after ActivateConnection, "
                        + "attaching signal handler."
                    )
                    vpn_interface = self.get_vpn_interface(self.vpn_name)
                    self.vpn_signal_handler(vpn_interface, is_iface=True)
                else:
                    logger.error(
                        "Dbus exception: {}".format(e)
                    )
                pass

    def vpn_signal_handler(self, conn, is_iface=False):
        iface = conn
        if not is_iface:
            proxy = self.bus.get_object(
                "org.freedesktop.NetworkManager", conn
            )
            iface = dbus.Interface(
                proxy, "org.freedesktop.NetworkManager.VPN.Connection"
            )
        try:
            logger.info("Interface settings: {}".format(iface.GetSettings()))
        except dbus.exceptions.DBusException:
            logger.info("No GetSettings() for active connection {}".format(
                iface.GetAll()["Id"])
            )
        iface.connect_to_signal(
            "VpnStateChanged", self.on_vpn_state_changed
        )


DBusGMainLoop(set_as_default=True)
loop = GLib.MainLoop()
ins = ProtonVPNReconnector("proton0", loop)
loop.run()
