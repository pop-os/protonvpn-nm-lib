import dbus

from ..logger import logger


class DbusGetWrapper():
    NETWORK_MANAGER_INTERFACE_NAME = "/org/freedesktop/NetworkManager"

    def search_for_connection(
        self, name, is_active=False, is_interface=False,
        return_settings_path=False, return_device_path=False,
        return_active_conn_path=False
    ):
        """Search for specified connection.

        Args:
            name (string): connection name
            is_active (bool): check for active conns
            is_interface (bool): if name is an interface
            return_settings_path (bool): return settings path
            return_device_path (bool): return device path
            return_active_conn_path (bool): return active connection
            path. This returns only if is_active is also True.
        Returns:
           Dict: with specified content. Connection ID is returned always.
           To extract contents of dict, use the following keys:
            - connection_id
            - settings_path
            - device_path
            - active_conn_path
        """
        if is_active:
            connection_list = self.get_all_active_conns()
        else:
            connection_list = self.get_all_conns()

        for iterated_connection in connection_list:
            if is_active:
                conn_props = self.get_active_conn_props(
                    iterated_connection
                )
                iterated_connection = conn_props["Connection"]

            all_connection_properties = self.get_all_conn_settings(
                iterated_connection
            )
            connection_id = str(all_connection_properties["connection"]["id"])

            try:
                dbus_interface = None
                if is_interface:
                    dbus_interface = str(
                        all_connection_properties[
                            "connection"
                        ]["interface-name"]
                    )
            except KeyError:
                pass
            else:
                if (
                    name == connection_id
                    or name == dbus_interface
                ):
                    return_list = {"connection_id": connection_id}
                    if return_settings_path:
                        return_list["settings_path"] = iterated_connection
                    if return_device_path:
                        return_list["device_path"] = self.get_connection_device_path( # noqa
                            iterated_connection
                        )
                    if return_active_conn_path and is_active:
                        return_list["active_conn_path"] = self.get_active_connection( # noqa
                            get_by_settings_path=iterated_connection
                        )

                    return return_list

        return {}

    def get_connection_device_path(self, connection_settings_path):
        """Get path to connection device.

        Args:
            connection_settings_path (string): connection settings path

        Returns:
            string | None: either path to device if found
            or None if device was not found not.
        """
        devices = self.get_network_manager_properties()["AllDevices"]
        for device in devices:
            device_props_interface = self.get_dbus_object_proprties_interface(
                device
            )
            devices_props = device_props_interface.GetAll(
                "org.freedesktop.NetworkManager.Device"
            )
            device_available_conns = devices_props["AvailableConnections"]
            if len(device_available_conns) > 0:
                conn_settings_path = str(device_available_conns.pop())
                if connection_settings_path == conn_settings_path:
                    return device

        return None

    def activate_connection(self, connection_settings_path, device_path):
        """Activate existing connection.

        Args:
            connection_settings_path (string): path to connection settings
            device_path (string): path to device

        Returns:
            string | None: either path to active connection
            if connection was successfully activated
            or None if not.
        """
        nm_interface = self.get_network_manager_interface()
        active_conn_path = nm_interface.ActivateConnection(
            connection_settings_path,
            device_path,
            "/"
        )

        return None if not active_conn_path else active_conn_path

    def disconnect_connection(self, connection_path):
        """Disconnect active connection.

        Args:
            connection_path (string): path to active connection
        """
        nm_interface = self.get_network_manager_interface()
        nm_interface.DeactivateConnection(connection_path)

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

    def get_vpn_interface(self, return_properties=False):
        """Get VPN connection interface based on virtual device name.

        Args:
            virtual_device_name (string): virtual device name (ie: proton0)

        Returns:
            dbus.proxies.Interface: to ProtonVPN connection
        """
        logger.info(
            "Get connection interface from '{}' virtual device.".format(
                self.virtual_device_name
            )
        )
        connections = self.get_all_conns()
        for connection in connections:
            try:
                all_settings, iface = self.get_all_conn_settings(
                    connection, return_iface=True
                )
            except dbus.exceptions.DBusException as e:
                logger.exception(e)
                continue
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

    def get_active_connection(
        self, get_by_id=None, get_by_interface=False,
        get_by_settings_path=False, get_by_device_path=False
    ):
        """Get interface of active
        connection with default route(s) if no options
        were specified. Else returns active connection
        for the specified option.
        All options are mutually exclusive.

        Args:
            get_by_id (string): connection id
            get_by_interface (string): connection interface
            get_by_settings_path (string): connection settings path
            get_by_device_path (string): connection device path

        Returns:
            string: active connection path
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
            except dbus.exceptions.DBusException as e:
                logger.exception(e)
                continue

            if get_by_id and str(active_conn_props["Id"]) == get_by_id:
                return active_conn
            elif get_by_settings_path and str(active_conn_props["Connection"]) == get_by_settings_path: # noqa
                return active_conn
            elif get_by_device_path and str(active_conn_props["Devices"].pop()) == get_by_device_path: # noqa
                return active_conn
            elif (
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
        iface = self.get_dbus_object_proprties_interface(active_conn)
        return iface.GetAll(
            "org.freedesktop.NetworkManager.Connection.Active"
        )

    def get_all_conns(self):
        """Get all existing connections.

        Returns:
            list(string): yields path to all connections
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
            list(string): yields path to active connections
        """
        iface = self.get_dbus_object_proprties_interface(
            self.NETWORK_MANAGER_INTERFACE_NAME
        )

        all_active_conns_list = iface.Get(
            "org.freedesktop.NetworkManager", "ActiveConnections"
        )
        for active_conn in all_active_conns_list:
            yield active_conn

    def get_network_manager_proxy_object(self):
        """Get network manager proxy object.

        Returns:
            dbus.proxies.ProxyObject: network manager proxy object
        """
        proxy = self.bus.get_object(
            "org.freedesktop.NetworkManager",
            self.NETWORK_MANAGER_INTERFACE_NAME
        )
        return proxy

    def get_network_manager_interface(self):
        """Get network manager interface.

        Returns:
            dbus.proxies.Interface: network manager interface
        """
        nm_proxy_object = self.get_network_manager_proxy_object()

        logger.info("Getting NetworkManager interface")
        nm_interface = dbus.Interface(
            nm_proxy_object, "org.freedesktop.NetworkManager"
        )
        return nm_interface

    def get_network_manager_properties_interface(self):
        """Get network manager properties interface.

        Returns:
            dbus.proxies.Interface: network manager proprties interface
        """
        nm_proxy_object = self.get_network_manager_proxy_object()
        nm_interface = dbus.Interface(
            nm_proxy_object, "org.freedesktop.DBus.Properties"
        )
        return nm_interface

    def get_network_manager_properties(self):
        """Get all network manager properties.

        Returns:
            Dict: contains all network manager properties
        """
        nm_prop_interface = self.get_network_manager_properties_interface()

        nm_properties = nm_prop_interface.GetAll(
            "org.freedesktop.NetworkManager"
        )

        return nm_properties

    def get_dbus_object_proprties_interface(self, object_path):
        """Get properties interface for specified object_path.

        Args:
            object_path (str): path to object

        Returns:
            dbus.proxies.Interface: properties interface of specified object
        """
        proxy_object = self.bus.get_object(
            "org.freedesktop.NetworkManager", object_path
        )

        properties_interface = dbus.Interface(
            proxy_object, "org.freedesktop.DBus.Properties"
        )
        return properties_interface
