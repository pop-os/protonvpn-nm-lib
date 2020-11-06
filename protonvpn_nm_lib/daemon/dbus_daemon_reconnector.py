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
from protonvpn_nm_lib.constants import VIRTUAL_DEVICE_NAME
from protonvpn_nm_lib.logger import logger
from protonvpn_nm_lib.services.connection_state_manager import \
    ConnectionStateManager
from protonvpn_nm_lib.services.dbus_get_wrapper import DbusGetWrapper
from protonvpn_nm_lib.services.killswitch_manager import KillSwitchManager
from protonvpn_nm_lib.services.user_configuration_manager import \
    UserConfigurationManager


class ProtonVPNReconnector(ConnectionStateManager, DbusGetWrapper):
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
        self.user_conf_manager = UserConfigurationManager()
        self.ks_manager = KillSwitchManager(self.user_conf_manager)
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
        logger.info("Initialized Dbus daemon manager")

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
            self.save_connected_time()

            logger.info(
                "ProtonVPN with virtual device '{}' is running.".format(
                    self.virtual_device_name
                )
            )
            self.ks_manager.manage("post_connection")
        elif state == 7 and reason == 2:
            logger.info("ProtonVPN connection was manually disconnected.")
            self.failed_attempts = 0

            vpn_iface, settings = self.get_vpn_interface(True)

            logger.info("User prior disconnecting: {}".format(
                getpass.getuser())
            )

            self.remove_connection_metadata()

            try:
                vpn_iface.Delete()
            except dbus.exceptions.DBusException as e:
                logger.error(
                    "[!] Unable to remove connection. "
                    + "Exception: {}".format(e)
                )
            else:
                logger.info("ProtonVPN connection has been manually removed.")
                # if killswitch soft then:
                #   disable killswitch
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
            "\n\n---------------------- "
            "Daemon reconnector monitoring VPN connection"
            " ----------------------\n"
            + "-Virtual device being monitored: {},".format(
                self.virtual_device_name
            ) + "\n"
            + "-Reattempting up to {} times with {} ".format(
                self.max_attempts, self.delay
            ) + "ms between retries\n"
        )
        vpn_interface = self.get_vpn_interface()
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
            server_ip = self.get_server_ip()
            server_ip = server_ip[0]
            logger.info("Reconnecting to server IP \"{}\"".format(server_ip))
            if is_protonvpn and state == 1:
                logger.info("ProtonVPN connection is being prepared.")
                self.ks_manager.manage("pre_connection", server_ip=server_ip)
                self.vpn_signal_handler(conn)
            else:
                logger.info("User prior creating new connection: {}".format(
                    getpass.getuser())
                )
                try:
                    self.ks_manager.manage(
                        "pre_connection", server_ip=server_ip
                    )
                    self.setup_new_protonvpn_conn(
                        self.get_active_connection(), vpn_interface
                    )
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
ins = ProtonVPNReconnector(VIRTUAL_DEVICE_NAME, loop)
loop.run()
