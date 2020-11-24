import dbus

from ..logger import logger


class DbusGetWrapper():

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

    def get_network_manager(self):
        """Get network manager dbus interface.

        Returns:
            dbus.Interface(dbus.Proxy): to ProtonVPN connection
        """
        logger.info("Getting NetworkManager interface")
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager", "/org/freedesktop/NetworkManager"
        )
        return dbus.Interface(proxy, "org.freedesktop.NetworkManager")

    def get_vpn_interface(self, return_properties=False):
        """Get VPN connection interface based on virtual device name.

        Args:
            virtual_device_name (string): virtual device name (ie: proton0)
        Returns:
            dbus.Interface(dbus.Proxy): to ProtonVPN connection
        """
        logger.info(
            "Get connection interface from '{}' virtual device.".format(
                self.virtual_device_name
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
            if all_settings["connection"]["type"] == "vpn":
                vpn_virtual_device = False
                try:
                    vpn_virtual_device = all_settings["vpn"]["data"]["dev"]
                except KeyError:
                    logger.debug(
                        "VPN \"{}\" is missing \"dev\" parameter", format(
                            all_settings["connection"]["id"]
                        )
                    )
                    continue
                except Exception as e:
                    logger.exception(
                        "[!] Unhandled exceptions: {}\n".format(e)
                        + "Connection information: {}".format(all_settings)
                    )
                    continue

                if vpn_virtual_device == self.virtual_device_name:
                    logger.info(
                        "Found virtual device "
                        + "'{}'.".format(self.virtual_device_name)
                    )

                    if return_properties:
                        return (iface, all_settings)
                    return iface

        logger.error(
            "[!] Could not find interface belonging to '{}'.".format(
                self.virtual_device_name
            )
        )
        return None

    def get_active_connection(self):
        """Get interface of active
        network connection with default route(s).

        Returns:
            string: active connection path that has default route(s)
        """
        logger.info("Getting active connection interface")
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

        return None

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
