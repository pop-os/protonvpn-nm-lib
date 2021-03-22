from .....enums import ProtocolImplementationEnum
from .....logger import logger
import gi

gi.require_version("NM", "1.0")
from gi.repository import NM


class NMPlugin:

    @staticmethod
    def import_vpn_config(vpn_configuration):
        plugin_info = NM.VpnPluginInfo
        vpn_plugin_list = plugin_info.list_load()

        connection = None
        plugin_name = None

        with vpn_configuration as filename:
            for plugin in vpn_plugin_list:
                plugin_editor = plugin.load_editor_plugin()
                # return a NM.SimpleConnection (NM.Connection)
                # https://lazka.github.io/pgi-docs/NM-1.0/classes/SimpleConnection.html
                try:
                    connection = plugin_editor.import_(filename)
                    plugin_name = plugin.props.name
                except gi.repository.GLib.Error:
                    pass

        if connection is None:
            raise NotImplementedError(
                "Support for given configuration is not implemented"
            )

        # https://lazka.github.io/pgi-docs/NM-1.0/classes/Connection.html#NM.Connection.normalize
        if connection.normalize():
            logger.info("Connection was normalized")

        return connection, ProtocolImplementationEnum(plugin_name)
