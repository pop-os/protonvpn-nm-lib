import os
from getpass import getuser

import gi

gi.require_version("NM", "1.0")
from gi.repository import NM, GLib

from .. import exceptions
from ..constants import CONFIG_STATUSES, ENV_CI_NAME, VIRTUAL_DEVICE_NAME
from ..enums import (ConnectionMetadataEnum, KillswitchStatusEnum,
                     UserSettingStatusEnum)
from ..logger import logger
from ..services.connection_state_manager import ConnectionStateManager
from . import capture_exception
from .plugin_manager import PluginManager


class ConnectionManager(ConnectionStateManager):
    def __init__(
        self,
        virtual_device_name=VIRTUAL_DEVICE_NAME
    ):
        self.virtual_device_name = virtual_device_name

    def add_connection(
        self, filename, username, password,
        delete_cached_cert, domain,
        user_conf_manager, ks_manager, ipv6_lp_manager,
        entry_ip
    ):
        """Setup and add ProtonVPN connection.

        Args:
            filename (string): certificate filename
            username (string): openvpn username
            password (string): openvpn password
            delete_cached_cert (method): method that delete cached cert
        """
        logger.info("Adding VPN connection")
        if not isinstance(filename, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(filename))

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
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(username))

            logger.error(
                "[!] TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif not isinstance(password, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(password))
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
            delete_cached_cert("no_existing_cert.ovpn")
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.exception(
                "[!] NotImplementedError: {}".format(e)
            )
            capture_exception(e)
            err_msg = "Expects object method, {} was not passed".format(
                delete_cached_cert
            )
            raise NotImplementedError(err_msg)

        # https://lazka.github.io/pgi-docs/NM-1.0/classes/Client.html
        client = NM.Client.new(None)
        main_loop = GLib.MainLoop()

        connection = PluginManager.import_connection_from_file(
            filename
        )
        vpn_settings = connection.get_setting_vpn()
        conn_settings = connection.get_setting_connection()

        self.make_vpn_user_owned(conn_settings)
        self.set_custom_connection_id(conn_settings)
        self.add_vpn_credentials(vpn_settings, username, password)
        self.add_server_certificate_check(vpn_settings, domain)
        self.apply_virtual_device_type(vpn_settings, filename)
        self.dns_manager(connection, user_conf_manager.dns)
        ipv6_lp_manager.manage("enable")
        if user_conf_manager.killswitch == KillswitchStatusEnum.HARD: # noqa
            ks_manager.manage("pre_connection", server_ip=entry_ip)

        client.add_connection_async(
            connection,
            True,
            None,
            self.dynamic_callback,
            dict(
                callback_type="add",
                main_loop=main_loop,
                conn_name=connection.get_id(),
            )
        )

        main_loop.run()
        if not os.environ.get(ENV_CI_NAME):
            delete_cached_cert(filename)

    def make_vpn_user_owned(self, connection_settings):
        # returns NM.SettingConnection
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/SettingConnection.html#NM.SettingConnection
        logger.info("Making VPN connection be user owned")
        connection_settings.add_permission(
            "user",
            getuser(),
            None
        )

    def set_custom_connection_id(self, connection_settings):
        id_suffix_dict = self.get_connection_metadata()
        id_suffix = id_suffix_dict[ConnectionMetadataEnum.SERVER]
        connection_settings.props.id = "ProtonVPN " + id_suffix

    def add_vpn_credentials(self, vpn_settings,
                            openvpn_username, openvpn_password):
        """Add OpenVPN credentials to ProtonVPN connection.

        Args:
            vpn_settings (NM.SettingVpn): NM.SettingVPN object
            openvpn_username (string): openvpn/ikev2 username
            openvpn_password (string): openvpn/ikev2 password
        """
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
            capture_exception(e)
            raise exceptions.AddConnectionCredentialsError(e)

    def dns_manager(self, connection, dns_setting):
        """Apply dns configurations to ProtonVPN connection.

        Args:
            connection (NM.SimpleConnection): vpn connection object
            dns_setting (tuple(int, [])): contains dns configurations
        """
        logger.info("DNS configs: {}".format(dns_setting))
        dns_status, custom_dns = dns_setting

        if dns_status not in CONFIG_STATUSES:
            raise Exception("Incorrect status configuration")

        ipv4_config = connection.get_setting_ip4_config()
        ipv6_config = connection.get_setting_ip6_config()

        if dns_status == UserSettingStatusEnum.ENABLED:
            logger.info("Applying automatic DNS")
            ipv4_config.props.dns_priority = -50
            ipv6_config.props.dns_priority = -50
        else:
            ipv4_config.props.ignore_auto_dns = True
            ipv6_config.props.ignore_auto_dns = True

            if dns_status == UserSettingStatusEnum.CUSTOM:
                logger.info("Applying custom DNS: {}".format(custom_dns))
                ipv4_config.props.dns_priority = -50
                ipv6_config.props.dns_priority = -50

                ipv4_config.props.dns = custom_dns
            else:
                logger.info("DNS managemenet disallowed")

    def add_server_certificate_check(self, vpn_settings, domain):
        logger.info("Adding server certificate check")
        appened_domain = "name:" + domain
        try:
            vpn_settings.add_data_item(
                "verify-x509-name", appened_domain
            )
        except Exception as e:
            logger.exception(
                "[!] AddServerCertificateCheckError: {}. ".format(e)
                + "Raising exception."
            )
            capture_exception(e)
            raise exceptions.AddServerCertificateCheckError(e)

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
        self.save_connected_time()

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

    def remove_connection(
        self,
        user_conf_manager,
        ks_manager,
        ipv6_lp_manager,
        reconector_manager
    ):
        """Stop and remove ProtonVPN connection."""
        logger.info("Removing VPN connection")
        client = NM.Client.new(None)
        main_loop = GLib.MainLoop()
        conn = self.get_proton_connection("all_connections", client)

        if len(conn) < 2 and conn[0] is False:
            logger.info(
                "[!] ConnectionNotFound: Connection not found, "
                + "raising exception"
            )
            raise exceptions.ConnectionNotFound(
                "ProtonVPN connection was not found"
            )

        self.stop_connection(client)

        conn_name = conn[1]
        conn = conn[0]
        reconector_manager.stop_daemon_reconnector()
        self.remove_connection_metadata()

        # conn is a NM.RemoteConnection
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/RemoteConnection.html#NM.RemoteConnection
        ipv6_lp_manager.manage("disable")

        if user_conf_manager.killswitch == KillswitchStatusEnum.SOFT: # noqa
            ks_manager.manage("disable")

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

    def display_connection_status(self, from_connections="active_connections"):
        connection_exists = self.get_proton_connection(from_connections)

        if not connection_exists[0]:
            return False

        return self.get_connection_metadata()

    def dynamic_callback(self, client, result, data):
        """Dynamic callback method.

        Args:
            client (NM.Client): nm client object
            result (Gio.AsyncResult): function
            data (dict): optional extra data
        """
        callback_type = data.get("callback_type")
        logger.info("Callback type: \"{}\"".format(callback_type))
        main_loop = data.get("main_loop")
        conn_name = data.get("conn_name")

        try:
            callback_type_dict = dict(
                remove=dict(
                    finish_function=client.delete_finish,
                    msg="removed"
                )
            )
        except AttributeError:
            callback_type_dict = dict(
                add=dict(
                    finish_function=client.add_connection_finish,
                    msg="added"
                ),
                start=dict(
                    finish_function=client.activate_connection_finish,
                    msg="started"
                ),
                stop=dict(
                    finish_function=client.deactivate_connection_finish,
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
        except Exception as e:
            logger.exception("[!] Exception: {}".format(e))

        main_loop.quit()

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
            except Exception as e:
                logger.exception("[!] Unknown exception: {}".format(e))
                capture_exception(e)

            try:
                index = virtual_dev_type_list.index(dev_type)
            except (ValueError, KeyError, TypeError) as e:
                logger.exception("[!] IllegalVirtualDevice: {}".format(e))
                raise exceptions.IllegalVirtualDevice(
                    "Only {} are permitted, though \"{}\" ".format(
                        ' and '.join(virtual_dev_type_list), dev_type
                    ) + " was provided"
                )
            except Exception as e:
                logger.exception("[!] Unknown exception: {}".format(e))
                capture_exception(e)
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
