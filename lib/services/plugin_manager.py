from lib import exceptions
import gi
gi.require_version("NM", "1.0")
from gi.repository import NM


class PluginManager():
    PROTOCOL_DICT = dict(
        openvpn=["tcp", "udp"],
        strongswan=["ikev2"]
    )

    def __init__(self, virtual_device_name="proton0"):
        self.virtual_device_name = virtual_device_name

    def import_connection_from_ovpn(self, filename, vpn_protocol="tcp"):
        """Import connection form .ovpn file"""
        protocol_implementation_type = self.get_protocol_implementation_type(
            vpn_protocol
        )
        editor_plugin = self.get_matching_plugin(protocol_implementation_type)

        try:
            # return a NM.SimpleConnection (NM.Connection)
            # https://lazka.github.io/pgi-docs/NM-1.0/classes/SimpleConnection.html
            connection = editor_plugin.import_(filename)
        except Exception:
            raise exceptions.ImportConnectionError(
                "The provided file \"{}\" is invalid".format(filename)
            )
        else:
            # Does some basic normalization and
            # fixup of well known inconsistencies and deprecated fields.
            # If the connection was modified in any way, then return True
            # https://lazka.github.io/pgi-docs/NM-1.0/classes/Connection.html#NM.Connection.normalize
            if connection.normalize():
                print("Connection was normalized")
            return connection

    def get_protocol_implementation_type(self, vpn_protocol):
        """Find and return protocol implementation type"""
        for plugin_name, protocol_types in self.PROTOCOL_DICT.items():
            if vpn_protocol.lower() in protocol_types:
                return plugin_name

        raise exceptions.IllegalVPNProtocol("Selected protocol was not found")

    def get_matching_plugin(self, protocol_implementation_type):
        """Find and return matching plugin"""
        plugin_info = NM.VpnPluginInfo

        # returns [NM.VpnPluginInfo] plugins
        vpn_plugin_list = plugin_info.list_load()

        # returns the first NM.VpnPluginInfo
        protocol_plugin = plugin_info.list_find_by_name(
            vpn_plugin_list,
            protocol_implementation_type
        )

        if protocol_plugin is None:
            raise exceptions.ProtocolPluginNotFound(
                "The \"{}\" ".format(protocol_implementation_type)
                + "protocol was not found"
            )

        # Returns NM.VpnEditorPlugin
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/VpnEditorPlugin.html
        return protocol_plugin.load_editor_plugin()
