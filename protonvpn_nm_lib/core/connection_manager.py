from getpass import getuser

import gi
import requests

gi.require_version("NM", "1.0")
from gi.repository import NM, GLib

from .. import exceptions
from ..constants import CONFIG_STATUSES, VIRTUAL_DEVICE_NAME
from ..enums import (ConnectionMetadataEnum, KillSwitchManagerActionEnum,
                     KillswitchStatusEnum, MetadataEnum,
                     NetworkManagerConnectionTypeEnum, UserSettingStatusEnum)
from ..logger import logger
from .connection_state_manager import ConnectionStateManager
from . import capture_exception
from .plugin_manager import PluginManager


class ConnectionManager(ConnectionStateManager):
    def __init__(
        self,
        virtual_device_name=VIRTUAL_DEVICE_NAME
    ):
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/Client.html
        self.client = NM.Client.new(None)
        self.main_loop = GLib.MainLoop()
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
                "TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif len(filename) == 0:
            err_msg = "A valid filename must be provided"

            logger.error(
                "ValueError: {}".format(err_msg)
            )
            raise ValueError(err_msg)

        if not isinstance(username, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(username))

            logger.error(
                "TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif not isinstance(password, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(password))
            logger.error(
                "TypeError: {}".format(err_msg)
            )
            raise TypeError(err_msg)

        elif not username.strip() or not password.strip():
            err_msg = "Both username and password must be provided"
            logger.error(
                "ValueError: {}".format(err_msg)
            )
            raise ValueError(err_msg)

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
        self.dns_manager(connection, user_conf_manager)
        if ipv6_lp_manager.enable_ipv6_leak_protection:
            ipv6_lp_manager.manage(KillSwitchManagerActionEnum.ENABLE)
        if user_conf_manager.killswitch == KillswitchStatusEnum.HARD: # noqa
            ks_manager.manage(
                KillSwitchManagerActionEnum.PRE_CONNECTION,
                server_ip=entry_ip
            )

        self.client.add_connection_async(
            connection,
            True,
            None,
            self.dynamic_callback,
            dict(
                callback_type="add",
                # main_loop=self.main_loop,
                conn_name=connection.get_id(),
            )
        )

        self.main_loop.run()

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
        id_suffix_dict = self.get_connection_metadata(MetadataEnum.CONNECTION)
        id_suffix = id_suffix_dict[ConnectionMetadataEnum.SERVER.value]
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
                "AddConnectionCredentialsError: {}. ".format(e)
                + "Raising exception."
            )
            capture_exception(e)
            raise exceptions.AddConnectionCredentialsError(e)

    def dns_manager(self, connection, user_conf_manager):
        """Apply dns configurations to ProtonVPN connection.

        Args:
            connection (NM.SimpleConnection): vpn connection object
            dns_setting (tuple(int, [])): contains dns configurations
        """
        dns_status, custom_dns = user_conf_manager.dns
        logger.info("DNS configs: {} - {}".format(
            dns_status, custom_dns
        ))

        if dns_status not in CONFIG_STATUSES:
            raise Exception("Incorrect status configuration")

        if dns_status == UserSettingStatusEnum.DISABLED:
            dns_status = UserSettingStatusEnum.ENABLED

        ipv4_config = connection.get_setting_ip4_config()
        ipv6_config = connection.get_setting_ip6_config()

        if dns_status == UserSettingStatusEnum.ENABLED:
            logger.info("Applying automatic DNS")
            ipv4_config.props.dns_priority = -50
            ipv6_config.props.dns_priority = -50
        else:
            custom_dns = custom_dns[0]
            ipv4_config.props.ignore_auto_dns = True
            ipv6_config.props.ignore_auto_dns = True

            if dns_status == UserSettingStatusEnum.CUSTOM:
                logger.info("Applying custom DNS: {}".format(custom_dns))
                ipv4_config.props.dns_priority = -50
                ipv6_config.props.dns_priority = -50
                for ip in custom_dns:
                    user_conf_manager.is_valid_ip(ip)
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
                "AddServerCertificateCheckError: {}. ".format(e)
                + "Raising exception."
            )
            capture_exception(e)
            raise exceptions.AddServerCertificateCheckError(e)

    def start_connection(self):
        """Start ProtonVPN connection."""
        logger.info("Starting VPN connection")

        conn = self.get_protonvpn_connection(
            NetworkManagerConnectionTypeEnum.ALL
        )

        if len(conn) < 1:
            logger.error(
                "ConnectionNotFound: Connection not found, "
                + "raising exception"
            )
            raise exceptions.ConnectionNotFound(
                "ProtonVPN connection was not found"
            )

        conn_name = conn[1]
        conn = conn[0]

        self.client.activate_connection_async(
            conn,
            None,
            None,
            None,
            self.dynamic_callback,
            dict(
                callback_type="start",
                # main_loop=self.main_loop,
                conn_name=conn_name
            )
        )

        self.main_loop.run()
        self.save_connected_time()

    def stop_connection(self):
        """Stop ProtonVPN connection.

        Args(optional):
            client (NM.Client): new NetworkManager Client object
        """
        logger.info("Stopping VPN connection")
        conn = self.get_protonvpn_connection(
            NetworkManagerConnectionTypeEnum.ACTIVE
        )

        if len(conn) < 1:
            logger.info("Connection not found")
            return False

        conn_name = conn[1]
        conn = conn[0]

        self.client.deactivate_connection_async(
            conn,
            None,
            self.dynamic_callback,
            dict(
                callback_type="stop",
                # main_loop=self.main_loop,
                conn_name=conn_name
            )
        )

        self.main_loop.run()

    def remove_connection(
        self,
        user_conf_manager,
        ks_manager,
        ipv6_lp_manager,
        reconector_manager
    ):
        """Stop and remove ProtonVPN connection."""
        logger.info("Removing VPN connection")
        conn = self.get_protonvpn_connection(
            NetworkManagerConnectionTypeEnum.ALL
        )

        if len(conn) < 1:
            logger.info(
                "ConnectionNotFound: Connection not found, "
                + "raising exception"
            )
            raise exceptions.ConnectionNotFound(
                "ProtonVPN connection was not found"
            )

        self.stop_connection()

        conn_name = conn[1]
        conn = conn[0]
        reconector_manager.stop_daemon_reconnector()
        self.remove_connection_metadata(MetadataEnum.CONNECTION)

        # conn is a NM.RemoteConnection
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/RemoteConnection.html#NM.RemoteConnection
        ipv6_lp_manager.manage(KillSwitchManagerActionEnum.DISABLE)

        if user_conf_manager.killswitch == KillswitchStatusEnum.SOFT: # noqa
            ks_manager.manage(KillSwitchManagerActionEnum.DISABLE)

        conn.delete_async(
            None,
            self.dynamic_callback,
            dict(
                callback_type="remove",
                # main_loop=self.main_loop,
                conn_name=conn_name
            )
        )

        self.main_loop.run()

    def is_internet_connection_available(self, ks_status):
        logger.info("Checking internet connectivity")
        if ks_status == KillswitchStatusEnum.HARD:
            return

        try:
            requests.get(
                "http://protonstatus.com/",
                timeout=5,
            )
        except requests.exceptions.Timeout as e:
            logger.exception("InternetConnectionError: {}".format(e))
            raise exceptions.InternetConnectionError(
                "No internet connection found, request timed out. "
                "Please make sure you are connected and retry."
            )
        except (requests.exceptions.RequestException, Exception) as e:
            logger.exception("InternetConnectionError: {}".format(e))
            raise exceptions.InternetConnectionError(
                "No internet connection. "
                "Please make sure you are connected and retry."
            )

    def is_api_reacheable(self, ks_status):
        logger.info("Checking API connectivity")

        if ks_status == KillswitchStatusEnum.HARD:
            return

        try:
            requests.get(
                "https://api.protonvpn.ch/tests/ping", timeout=10
            )
        except requests.exceptions.Timeout as e:
            logger.exception("APITimeoutError: {}".format(e))
            raise exceptions.APITimeoutError(
                "API unreacheable. Connection timed out."
            )
        except (requests.exceptions.RequestException, Exception) as e:
            logger.exception("UnreacheableAPIError: {}".format(e))
            raise exceptions.UnreacheableAPIError(
                "Couldn't reach Proton API."
                "This might happen due to connection issues or network blocks."
            )

    def dynamic_callback(self, client, result, data):
        """Dynamic callback method.

        Args:
            client (NM.Client): nm client object
            result (Gio.AsyncResult): function
            data (dict): optional extra data
        """
        callback_type = data.get("callback_type")
        logger.info("Callback type: \"{}\"".format(callback_type))
        # main_loop = data.get("main_loop")
        conn_name = data.get("conn_name")

        try:
            callback_type_dict = dict(
                remove=dict(
                    finish_function=NM.Client.delete_finish,
                    msg="removed"
                )
            )
        except AttributeError:
            callback_type_dict = dict(
                add=dict(
                    finish_function=NM.Client.add_connection_finish,
                    msg="added"
                ),
                start=dict(
                    finish_function=NM.Client.activate_connection_finish,
                    msg="started"
                ),
                stop=dict(
                    finish_function=NM.Client.deactivate_connection_finish,
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
            logger.exception("Exception: {}".format(e))

        self.main_loop.quit()

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
                logger.exception("VirtualDeviceNotFound: {}".format(e))
                raise exceptions.VirtualDeviceNotFound(
                    "No virtual device type was specified in .ovpn file"
                )
            except Exception as e:
                logger.exception("Unknown exception: {}".format(e))
                capture_exception(e)

            try:
                index = virtual_dev_type_list.index(dev_type)
            except (ValueError, KeyError, TypeError) as e:
                logger.exception("IllegalVirtualDevice: {}".format(e))
                raise exceptions.IllegalVirtualDevice(
                    "Only {} are permitted, though \"{}\" ".format(
                        ' and '.join(virtual_dev_type_list), dev_type
                    ) + " was provided"
                )
            except Exception as e:
                logger.exception("Unknown exception: {}".format(e))
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


    def get_protonvpn_connection(
        self, network_manager_connection_type
    ):
        """Get ProtonVPN connection.

        Args:
            connection_type (NetworkManagerConnectionTypeEnum):
                can either be:
                ALL - for all connections
                ACTIVE - only active connections
            client (NM.Client): nm client object (optional)

        Returns:
            list
        """
        logger.info("Getting VPN from \"{}\" connections".format(
            network_manager_connection_type
        ))
        return_conn = []

        connection_types = {
            NetworkManagerConnectionTypeEnum.ALL: self.client.get_connections,
            NetworkManagerConnectionTypeEnum.ACTIVE: self.client.get_active_connections # noqa
        }

        connections_list = connection_types[network_manager_connection_type]()

        for conn in connections_list:
            if conn.get_connection_type() == "vpn":
                conn_for_vpn = conn
                # conn can be either NM.RemoteConnection or NM.ActiveConnection
                if (
                    network_manager_connection_type
                    == NetworkManagerConnectionTypeEnum.ACTIVE
                ):
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
                None if len(return_conn) == 0 else return_conn
            )
        )
        return return_conn
