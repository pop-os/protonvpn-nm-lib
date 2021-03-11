import gi

from ...logger import logger
import dbus.exceptions
gi.require_version("NM", "1.0")
from gi.repository import NM, GLib
from ...enums import NetworkManagerConnectionTypeEnum
from ... import exceptions
from .nm_plugin import NMPlugin
from .setup_connection import SetupConnection


class NMClient:
    client = NM.Client.new(None)
    main_loop = GLib.MainLoop()

    def __init__(self, setup_connection=SetupConnection(), nm_plugin=NMPlugin):
        self.setup_connection = setup_connection
        self.nm_plugin = nm_plugin

    @property
    def virtual_device_name(self):
        return self.setup_connection.virtual_device_name

    @virtual_device_name.setter
    def virtual_device_name(self, new_virtual_device_name):
        self.setup_connection\
            .virtual_device_name = new_virtual_device_name

    @property
    def certificate_filepath(self):
        return self.setup_connection.certificate_filepath

    @certificate_filepath.setter
    def certificate_filepath(self, new_certificate_filepath):
        self.setup_connection\
            .certificate_filepath = new_certificate_filepath

    def add_connection(self, **kwargs):
        connection = self.nm_plugin.import_connection_from_file(
            self.setup_connection.certificate_filepath
        )
        self.setup_connection.connection = connection
        self.setup_connection.run_setup(**kwargs)
        self.client.add_connection_async(
            connection,
            True,
            None,
            self.dynamic_callback,
            dict(
                callback_type="add",
                conn_name=connection.get_id(),
            )
        )
        self.main_loop.run()

    def start_connection(self, connection):
        """Start ProtonVPN connection."""
        logger.info("Starting VPN connection")

        self.client.activate_connection_async(
            connection,
            None,
            None,
            None,
            self.dynamic_callback,
            dict(
                callback_type="start",
                conn_name=connection.get_id()
            )
        )
        self.main_loop.run()

    def remove_connection(self, protonvpn_connection):
        logger.info("Removing VPN connection")

        protonvpn_connection.delete_async(
            None,
            self.dynamic_callback,
            dict(
                callback_type="remove",
                conn_name=protonvpn_connection.get_id()
            )
        )
        self.main_loop.run()

    def stop_connection(self, protonvpn_connection):
        """Stop ProtonVPN connection.

        Args(optional):
            client (NM.Client): new NetworkManager Client object
        """
        logger.info("Stopping VPN connection")

        self.client.deactivate_connection_async(
            protonvpn_connection,
            None,
            self.dynamic_callback,
            dict(
                callback_type="stop",
                conn_name=protonvpn_connection.get_id()
            )
        )
        self.main_loop.run()

    def dynamic_callback(self, client, result, data):
        """Dynamic callback method.

        Args:
            client (NM.Client): nm client object
            result (Gio.AsyncResult): function
            data (dict): optional extra data
        """
        callback_type = data.get("callback_type")
        logger.info("Callback type: \"{}\"".format(callback_type))
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

    def get_protonvpn_connection(
        self, network_manager_connection_type
    ):
        """Get ProtonVPN connection.

        Args:
            connection_type (NetworkManagerConnectionTypeEnum):
                can either be:
                ALL - for all connections
                ACTIVE - only active connections

        Returns:
            if:
            - NetworkManagerConnectionTypeEnum.ALL: NM.RemoteConnection
            - NetworkManagerConnectionTypeEnum.ACTIVE: NM.ActiveConnection
        """
        logger.info("Getting VPN from \"{}\" connections".format(
            network_manager_connection_type
        ))
        protonvpn_connection = False

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
                    protonvpn_connection = conn
                    break
        logger.info(
            "VPN connection: {}".format(
                None if not len(protonvpn_connection) else protonvpn_connection
            )
        )
        return protonvpn_connection
