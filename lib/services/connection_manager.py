import os
import subprocess
from getpass import getuser

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM, GLib

from lib import exceptions
from lib.constants import ENV_CI_NAME, VIRTUAL_DEVICE_NAME
from lib.logger import logger
from lib.services.plugin_manager import PluginManager


class ConnectionManager():
    def __init__(
        self,
        virtual_device_name=VIRTUAL_DEVICE_NAME
    ):
        self.virtual_device_name = virtual_device_name

    def add_connection(self, filename, username, password, delete_cached_cert):
        """Setup and add ProtonVPN connection.

        Args:
            filename (string): certificate filename
            username (string): openvpn username
            password (string): openvpn password
            delete_cached_cert (method): method that delete cached cert
        """
        logger.info("Adding VPN connection")
        if not isinstance(filename, str):
            err_msg = "Incorrect object type, "
            + "str is expected but got {} instead".format(type(filename))

            logger.error(
                "[!] TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif not filename.strip():
            err_msg = "A valid filename must be provided"

            logger.error(
                "[!] ValueError: {}".format(err_msg)
            )
            raise ValueError(err_msg)

        if not isinstance(username, str):
            err_msg = "Incorrect object type, "
            + "str is expected but got {} instead".format(type(username))

            logger.error(
                "[!] TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif not isinstance(password, str):
            err_msg = "Incorrect object type, "
            + "str is expected but got {} instead".format(type(password))
            logger.error(
                "[!] TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif not username.strip() or not password.strip():
            err_msg = "Both username and password must be provided"
            logger.error(
                "[!] ValueError: {}".format(err_msg)
            )
            raise ValueError(err_msg)

        # Check that method to delete cached certificates is implemented
        try:
            delete_cached_cert("test")
        except FileNotFoundError:
            pass
        except Exception as e:
            err_msg = "Expects object method, {} was passed".format(
                delete_cached_cert
            )
            logger.exception(
                "[!] NotImplementedError: {}".format(e)
            )
            raise NotImplementedError(err_msg)

        # https://lazka.github.io/pgi-docs/NM-1.0/classes/Client.html
        client = NM.Client.new(None)
        main_loop = GLib.MainLoop()

        connection = PluginManager.import_connection_from_file(
            filename
        )
        vpn_settings = connection.get_setting_vpn()

        self.make_vpn_user_owned(connection)
        self.add_vpn_credentials(vpn_settings, username, password)
        self.apply_virtual_device_type(vpn_settings, filename)

        try:
            self.remove_connection()
        except exceptions.ConnectionNotFound:
            logger.info(
                "Attempted to remove connection. "
                + "No connection was found prior to adding a new one."
            )
            pass

        client.add_connection_async(
            connection,
            True,
            None,
            self.dynamic_callback,
            dict(
                callback_type="add",
                main_loop=main_loop,
                conn_name=connection.get_id(),
                delete_cached_cert=delete_cached_cert,
                filename=filename
            )
        )

        main_loop.run()

    def make_vpn_user_owned(self, connection):
        # returns NM.SettingConnection
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/SettingConnection.html#NM.SettingConnection
        logger.info("Making VPN connection be user owned")
        connection_settings = connection.get_setting_connection()
        connection_settings.add_permission(
            "user",
            getuser(),
            None
        )

    def add_vpn_credentials(self, vpn_settings,
                            openvpn_username, openvpn_password):
        # returns NM.SettingVpn if the connection contains one, otherwise None
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/SettingVpn.html
        logger.info("Adding OpenVPN credentials")
        try:
            vpn_settings.add_data_item("username", openvpn_username)
            vpn_settings.add_secret("password", openvpn_password)
        except Exception as e:
            logger.exception(
                "[!] AddConnectionCredentialsError: {}. ".format(e)
                + "Raising exception."
            )
            raise exceptions.AddConnectionCredentialsError(e)

    def start_connection(self):
        """Start ProtonVPN connection."""
        logger.info("Starting VPN connection")
        client = NM.Client.new(None)
        main_loop = GLib.MainLoop()

        conn = self.get_proton_connection("all_connections", client=client)

        if len(conn) < 2 and conn[0] is False:
            logger.error(
                "[!] ConnectionNotFound: Connection not found, "
                + "raising exception"
            )
            raise exceptions.ConnectionNotFound(
                "ProtonVPN connection was not found"
            )

        conn_name = conn[1]
        conn = conn[0]

        client.activate_connection_async(
            conn,
            None,
            None,
            None,
            self.dynamic_callback,
            dict(
                callback_type="start",
                main_loop=main_loop,
                conn_name=conn_name
            )
        )

        main_loop.run()

    def stop_connection(self, client=None):
        """Stop ProtonVPN connection.

        Args(optional):
            client (NM.Client): new NetworkManager Client object
        """
        logger.info("Stopping VPN connection")
        if not client:
            client = NM.Client.new(None)

        main_loop = GLib.MainLoop()

        conn = self.get_proton_connection("active_connections", client)

        if len(conn) < 2 and conn[0] is False:
            logger.info("Connection not found")
            return False

        conn_name = conn[1]
        conn = conn[0]

        client.deactivate_connection_async(
            conn,
            None,
            self.dynamic_callback,
            dict(
                callback_type="stop",
                main_loop=main_loop,
                conn_name=conn_name
            )
        )

        main_loop.run()

    def remove_connection(self):
        """Stop and remove ProtonVPN connection."""
        logger.info("Removing VPN connection")
        client = NM.Client.new(None)
        main_loop = GLib.MainLoop()
        conn = self.get_proton_connection("all_connections", client)

        if len(conn) < 2 and conn[0] is False:
            logger.error(
                "[!] ConnectionNotFound: Connection not found, "
                + "raising exception"
            )
            raise exceptions.ConnectionNotFound(
                "ProtonVPN connection was not found"
            )

        self.stop_connection(client)

        conn_name = conn[1]
        conn = conn[0]

        # conn is a NM.RemoteConnection
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/RemoteConnection.html#NM.RemoteConnection

        conn.delete_async(
            None,
            self.dynamic_callback,
            dict(
                callback_type="remove",
                main_loop=main_loop,
                conn_name=conn_name
            )
        )

        main_loop.run()

    def dynamic_callback(self, client, result, data):
        """Dynamic callback method.

        Args:
            client (NM.Client): nm client object
            result (Gio.AsyncResult): function
            data (dict): optional extra data
        """
        callback_type = data.get("callback_type")
        logger.info("Callback: \"{}\"".format(callback_type))
        main_loop = data.get("main_loop")
        conn_name = data.get("conn_name")
        delete_cached_cert = data.get("delete_cached_cert")
        filename = data.get("filename")

        try:
            callback_type_dict = dict(
                remove=dict(
                    finish_function=client.delete_finish,
                    exception=exceptions.RemoveConnectionFinishError,
                    msg="removed"
                )
            )
        except AttributeError:
            callback_type_dict = dict(
                add=dict(
                    finish_function=client.add_connection_finish,
                    exception=exceptions.AddConnectionFinishError,
                    msg="added"
                ),
                start=dict(
                    finish_function=client.activate_connection_finish,
                    exception=exceptions.StartConnectionFinishError,
                    msg="started"
                ),
                stop=dict(
                    finish_function=client.deactivate_connection_finish,
                    exception=exceptions.StopConnectionFinishError,
                    msg="stopped"
                )
            )

        try:
            (callback_type_dict[callback_type]["finish_function"])(result)
            msg = "The connection profile \"{}\" has been {}.".format(
                conn_name,
                callback_type_dict[callback_type]["msg"]
            )
            logger.info(msg)
            print(msg)
        except Exception as e:
            logger.exception(
                "[!] {}: {}".format(
                    callback_type_dict[callback_type]["exception"],
                    e
                )
            )
            raise (callback_type_dict[callback_type]["exception"])(e)

        if callback_type == "add":
            if not os.environ.get(ENV_CI_NAME):
                delete_cached_cert(filename)
        elif not callback_type == "stop":
            try:
                daemon_status = self.check_daemon_reconnector_status()
            except Exception as e:
                logger.exception("[!] Exception: {}".format(e))
                print(e)
            else:
                logger.info("Daemon status: {}".format(daemon_status))
                if not os.environ.get(ENV_CI_NAME):
                    self.daemon_manager(callback_type, daemon_status)
        main_loop.quit()

    def daemon_manager(self, callback_type, daemon_status):
        """Start/stop daemon reconnector.

        Args:
            callback_type (string): start, stop, remove
            daemon_status (int): 1 or 0
        """
        logger.info(
            "Managing daemon: cb_type-> \"{}\"; ".format(callback_type)
            + "daemon_status -> \"{}\"".format(daemon_status)
        )
        if callback_type == "start" and not daemon_status:
            self.call_daemon_reconnector("start")
        elif callback_type == "remove" and daemon_status:
            self.call_daemon_reconnector("stop")
            try:
                daemon_status = self.check_daemon_reconnector_status()
            except Exception as e:
                logger.exception("[!] Exception: {}".format(e))
                print(e)
            else:
                logger.info(
                    "Daemon status after stopping: {}".format(daemon_status)
                )

    def check_daemon_reconnector_status(self):
        """Checks the status of the daemon reconnector and starts the process
        only if it's not already running.

        Returns:
            int: indicates the status of the daemon process
        """
        logger.info("Checking daemon reconnector status")
        check_daemon = subprocess.run(
            ["systemctl", "status", "protonvpn_reconnect"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        decoded_stdout = check_daemon.stdout.decode()
        if (
            check_daemon.returncode == 3
        ) and ((
            "Active: inactive (dead)" in decoded_stdout
        ) or (
            "Active: failed" in decoded_stdout
        )):
            # Not running
            return 0
        elif (
            check_daemon.returncode == 0
        ) and (
            "Active: active (running)" in decoded_stdout
        ):
            # Already running
            return 1
        else:
            # Service threw an exception
            raise Exception(
                "[!] An error occurred while checking for ProtonVPN "
                + "reconnector service: "
                + "(Return code: {}; Exception: {} {})".format(
                    check_daemon.returncode, decoded_stdout,
                    check_daemon.stderr.decode().strip("\n")
                )
            )

    def call_daemon_reconnector(self, command=["start", "stop"]):
        """Makes calls to daemon reconnector to either
        start or stop the process.

        Args:
            command (string): to either start or stop the process
        """
        logger.info("Calling daemon reconnector")
        call_daemon = subprocess.run(
            ["systemctl", command, "protonvpn_reconnect"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        decoded_stdout = call_daemon.stdout.decode()
        decoded_stderr = call_daemon.stderr.decode().strip("\n")

        if not call_daemon.returncode == 0:
            msg = "[!] An error occurred while {}ing ProtonVPN ".format(
                command
            ) + "reconnector service: {} {}".format(
                decoded_stdout,
                decoded_stderr
            )
            logger.error(msg)
            print(msg)

    def extract_virtual_device_type(self, filename):
        """Extract virtual device type from .ovpn file.

        Args:
            filename (string): path to cached certificate
        Returns:
            string: "tap" or "tun", otherwise raises exception
        """
        logger.info("Extracting virtual device type")
        virtual_dev_type_list = ["tun", "tap"]

        with open(filename, "r") as f:
            content_list = f.readlines()
            dev_type = [dev.rstrip() for dev in content_list if "dev" in dev]
            try:
                dev_type = dev_type[0].split()[1]
            except IndexError as e:
                logger.exception("[!] VirtualDeviceNotFound: {}".format(e))
                raise exceptions.VirtualDeviceNotFound(
                    "No virtual device type was specified in .ovpn file"
                )

            try:
                index = virtual_dev_type_list.index(dev_type)
            except (ValueError, KeyError, TypeError) as e:
                logger.exception("[!] IllegalVirtualDevice: {}".format(e))
                raise exceptions.IllegalVirtualDevice(
                    "Only {} are permitted, though \"{}\" "
                    .format(' and '.join(virtual_dev_type_list), dev_type)
                    + "was provided"
                )
            else:
                return virtual_dev_type_list[index]

    def apply_virtual_device_type(self, vpn_settings, filename):
        """Apply virtual device type and name.

        Args:
            vpn_settings (SettingVpn): vpn settings object
            filename (string): path to cached certificate
        """
        logger.info("Applying virtual device type to VPN")
        virtual_device_type = self.extract_virtual_device_type(filename)

        # Changes virtual tunnel name
        vpn_settings.add_data_item("dev", self.virtual_device_name)
        vpn_settings.add_data_item("dev-type", virtual_device_type)

    def get_proton_connection(self, connection_type, client=None):
        """Get ProtonVPN connection.

        Args:
            connection_type (string): can either be
                all_connections - check all connections
                active_connections - check only active connections
            client (NM.Client): nm client object (optional)

        Returns:
            tuple: (bool|Empty) or (connection, connection_id)
        """
        logger.info("Getting VPN connection: \"{}\"".format(connection_type))
        return_conn = [False]

        if not client:
            client = NM.Client.new(None)

        connection_types = {
            "all_connections": client.get_connections,
            "active_connections": client.get_active_connections
        }

        all_cons = connection_types[connection_type]()

        for conn in all_cons:
            if conn.get_connection_type() == "vpn":
                conn_for_vpn = conn
                # conn can be either NM.RemoteConnection or NM.ActiveConnection
                if connection_type == "active_connections":
                    conn_for_vpn = conn.get_connection()

                vpn_settings = conn_for_vpn.get_setting_vpn()

                if (
                    vpn_settings.get_data_item("dev")
                    == self.virtual_device_name
                ):
                    return_conn = [conn, conn.get_id()]
                    break
        logger.info(
            "VPN connection: {}".format(
                None if return_conn[0] is False else return_conn
            )
        )
        return tuple(return_conn)
