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

import getpass

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from lib.logger import logger


class ProtonVPNReconnector(object):
    """Reconnects to VPN if disconnected not by user
    or when connecting to a new network.

    Params:
        virtual_device_name (string): Name of virtual device that will be used
        for ProtonVPNReconnector
        max_attempts (int): Maximum number of attempts ofreconnection VPN
        session on failures
        param delay (int): Miliseconds to wait before reconnecting VPN

    """
    def __init__(self, virtual_device_name, loop, max_attempts=5, delay=5000):
        self.virtual_device_name = virtual_device_name
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

    def on_network_state_changed(self, state):
        """Network status signal handler.

        Args:
            state (int): connection state (NMState)
        """
        logger.info("Network state changed: {}".format(state))
        if state == 70:
            self.vpn_monitor()

    def on_vpn_state_changed(self, state, reason):
        """VPN status signal handler.

        Args:
            reason (int): vpn connection state reason
                (NMActiveConnectionStateReason)
                0:  The reason for the active connection state change
                        is unknown.
                1:  No reason was given for the active connection state change.
                2:  The active connection changed state because the user
                        disconnected it.
                3:  The active connection changed state because the device it
                        was using was disconnected.
                4:  The service providing the VPN connection was stopped.
                5:  The IP config of the active connection was invalid.
                6:  The connection attempt to the VPN service timed out.
                7:  A timeout occurred while starting the service providing
                        the VPN connection.
                8:  Starting the service providing the VPN connection failed.
                9:  Necessary secrets for the connection were not provided.
                10: Authentication to the server failed.
                11: The connection was deleted from settings.
                12: Master connection of this connection failed to activate.
                13: Could not create the software device link.
                14: The device this connection depended on disappeared.
            state (int): vpn connection state
                (NMVpnConnectionState)
                0: The state of the VPN connection is unknown.
                1: The VPN connection is preparing to connect.
                2: The VPN connection needs authorization credentials.
                3: The VPN connection is being established.
                4: The VPN connection is getting an IP address.
                5: The VPN connection is active.
                6: The VPN connection failed.
                7: The VPN connection is disconnected.
        """
        logger.info(
            "State(NMVpnConnectionState): {} - ".format(state)
            + "Reason(NMActiveConnectionStateReason): {}".format(
                reason
            )
        )
        if state == 5:
            self.failed_attempts = 0
            logger.info(
                "ProtonVPN with virtual device '{}' is running.".format(
                    self.virtual_device_name
                )
            )
        elif state == 7 and reason == 2:
            self.failed_attempts = 0
            logger.info("ProtonVPN connection was manually disconnected.")
            vpn_iface, settings = self.get_vpn_interface(
                self.virtual_device_name, True
            )
            logger.info("User prior disconnecting: {}".format(
                getpass.getuser())
            )
            try:
                vpn_iface.Delete()
            except dbus.exceptions.DBusException as e:
                logger.error(
                    "[!] Unable to remove connection. "
                    + "Exception: {}".format(e)
                )
            else:
                logger.info("ProtonVPN connection has been manually removed.")
            finally:
                loop.quit()

        elif state in [6, 7]:
            # reconnect if haven't reached max_attempts
            if (
                not self.max_attempts
            ) or (
                self.failed_attempts < self.max_attempts
            ):
                logger.info("[!] Connection failed, attempting to reconnect.")
                self.failed_attempts += 1
                GLib.timeout_add(self.delay, self.vpn_monitor)
            else:
                logger.warning(
                    "[!] Connection failed, exceeded {} max attempts.".format(
                        self.max_attempts
                    )
                )
                self.failed_attempts = 0

    def get_network_manager(self):
        """Get network manager dbus interface.

        Returns:
            dbus.Interface(dbus.Proxy): to ProtonVPN connection
        """
        logger.info("Get NetworkManager DBUS interface")
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        return dbus.Interface(proxy, "org.freedesktop.NetworkManager")

    def get_vpn_interface(self, virtual_device_name, return_properties=False):
        """Get VPN connection interface based on virtual device name.

        Args:
            virtual_device_name (string): virtual device name (ie: proton0)
        Returns:
            dbus.Interface(dbus.Proxy): to ProtonVPN connection
        """
        logger.info(
            "Get connection interface from '{}' virtual device.".format(
                virtual_device_name
            )
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
                logger.info(
                    "Found virtual device "
                    + "'{}'.".format(virtual_device_name)
                )
                if return_properties:
                    return (iface, all_settings)
                return iface

        logger.error(
            "[!] Could not find interface belonging to '{}'.".format(
                virtual_device_name
            )
        )
        return None

    def get_active_connection(self):
        """Get interface of active
        network connection with default route(s).

        Returns:
            string: active connection path that has default route(s)
        """
        logger.info("Get active connection interface")
        active_connections = self.get_all_active_conns()
        logger.info(
            "All active conns in get_active_connection: {}".format(
                active_connections
            )
        )

        for active_conn in active_connections:
            try:
                active_conn_props = self.get_active_conn_props(active_conn)
            except TypeError as e:
                logger.error(
                    "No active connections were found. "
                    + "Exception: {}.".format(e)
                )
                return None

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
                    + "IPv4: {} / IPv6: {}.".format(
                        active_conn_props["Default"],
                        active_conn_props["Default6"]
                    )
                )
                return active_conn

    def get_all_conn_settings(self, conn, return_iface=False):
        """Get all settings of a connection.

        Args:
            conn (string): connection path
            return_iface (bool): also return the interface
        Returns:
            dict | tuple:
                dict: only properties are returned
                tuple: dict with properties is returned
                    and also the interface to the connection
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", conn
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.NetworkManager.Settings.Connection"
        )
        if return_iface:
            return (iface.GetSettings(), iface)

        return iface.GetSettings()

    def get_active_conn_props(self, active_conn):
        """Get active connection properties.

        Args:
            active_conn (string): active connection path
        Returns:
            dict: properties of an active connection
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", active_conn
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.DBus.Properties"
        )
        return iface.GetAll(
            "org.freedesktop.NetworkManager.Connection.Active"
        )

    def get_all_conns(self):
        """Get all existing connections.

        Returns:
            list(string): path to existing connections
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager/Settings"
        )
        iface = dbus.Interface(
            proxy, "org.freedesktop.NetworkManager.Settings"
        )
        all_conns = iface.ListConnections()
        for conn in all_conns:
            yield conn

    def get_all_active_conns(self):
        """Get all active connections.

        Returns:
            list(string): path to active connections
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        iface = dbus.Interface(proxy, "org.freedesktop.DBus.Properties")

        all_active_conns_list = iface.Get(
            "org.freedesktop.NetworkManager", "ActiveConnections"
        )
        for active_conn in all_active_conns_list:
            yield active_conn

    def is_protonvpn_being_prepared(self):
        """Checks ProtonVPN connection status.

        Returns:
            [0]: bool
            [1]: None | int (NMActiveConnectionState)
            [2]: None | string (active connection path)
        """
        all_active_conns = self.get_all_active_conns()

        protonvpn_conn_info = [False, None, None]
        for active_conn in all_active_conns:
            active_conn_props = self.get_active_conn_props(active_conn)
            vpn_all_settings = self.get_all_conn_settings(
                active_conn_props["Connection"]
            )
            if (
                active_conn_props["Type"] == "vpn"
            ) and (
                vpn_all_settings["vpn"]["data"]["dev"]
                == self.virtual_device_name
            ):
                protonvpn_conn_info[0] = True
                protonvpn_conn_info[1] = active_conn_props["State"]
                protonvpn_conn_info[2] = active_conn

        logger.info("ProtonVPN conn info: {}".format(protonvpn_conn_info))
        return tuple(protonvpn_conn_info)

    def check_active_vpn_conn(self, active_conn):
        """Check if active connection is VPN.

        Args:
            active_conn (string): active connection path
        Returns:
            [0]: bool
            [1]: None | dict with all connection settings
        """
        active_conn_all_settings = [False, None]

        try:
            active_conn_props = self.get_active_conn_props(active_conn)
        except dbus.exceptions.DBusException as e:
            logger.error(
                "Error occured while getting properties from active "
                + "connection: '{}'. Exception: {}.".format(active_conn, e)
            )
        else:
            if (
                active_conn_props["Type"] == "vpn"
            ) and (
                # NMActiveConnectionState
                # State 1 = a network connection is being prepared
                # State 2 = there is a connection to the network
                active_conn_props["State"] == 2
            ):
                active_conn_all_settings[0] = True
                active_conn_all_settings[1] = self.get_all_conn_settings(
                    active_conn_props["Connection"]
                )
        return active_conn_all_settings

    def setup_new_protonvpn_conn(self, active_con, vpn_interface):
        """Setup and start new ProtonVPN connection.

        Args:
            active_con (string): path to active connection
            vpn_interface (dbus.Proxy): proxy interface to vpn connection
        """
        new_con = self.get_network_manager().ActivateConnection(
            vpn_interface,
            dbus.ObjectPath("/"),
            active_con,
        )
        self.vpn_signal_handler(new_con)
        logger.info(
            "Starting new ProtonVPN connection with '{}'.".format(
                self.virtual_device_name
            )
        )

    def vpn_monitor(self):
        """Monitor and activate ProtonVPN connections."""
        logger.info(
            "____Monitoring connection "
            + "for {}, ".format(self.virtual_device_name)
            + "reattempting up to {} times with {} ".format(
                self.max_attempts, self.delay
            )
            + "ms between retries____"
        )
        vpn_interface = self.get_vpn_interface(self.virtual_device_name)
        active_con = self.get_active_connection()

        if active_con is None or vpn_interface is None:
            return

        is_active_conn_vpn, all_vpn_settings = self.check_active_vpn_conn(
            active_con
        )

        # Check if primary active connection was started by ProtonVPN client
        if (
            is_active_conn_vpn
        ) and (
            all_vpn_settings["vpn"]["data"]["dev"]
            == self.virtual_device_name
        ):
            logger.info("Primary connection via ProtonVPN.")
            self.vpn_signal_handler(active_con)
        else:
            is_protonvpn, state, conn = self.is_protonvpn_being_prepared()
            # Check if connection is being prepared
            if is_protonvpn and state == 1:
                logger.info("ProtonVPN connection is being prepared.")
                self.vpn_signal_handler(conn)
            else:
                logger.info("User prior creating new connection: {}".format(
                    getpass.getuser())
                )
                try:
                    self.setup_new_protonvpn_conn(active_con, vpn_interface)
                except dbus.exceptions.DBusException as e:
                    logger.error(
                        "Unable to start VPN connection: {}.".format(e)
                    )
                else:
                    logger.info(
                        "New ProtonVPN connection has been started "
                        + "from service."
                    )

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


DBusGMainLoop(set_as_default=True)
loop = GLib.MainLoop()
ins = ProtonVPNReconnector("proton0", loop)
loop.run()
