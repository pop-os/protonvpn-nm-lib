import os
import re

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM

from lib import exceptions
from lib.constants import SUPPORTED_PROTOCOLS


class PluginManager():
    def import_connection_from_file(self, filename):
        """Import connection from file

        Args:
            filename (string): path to file
        """
        vpn_protocol = self.extract_openvpn_protocol(filename)

        if not vpn_protocol:
            raise Exception("IKEv2/Wireguard protocols are not yet supported")

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

    def extract_openvpn_protocol(self, filename):
        """Extract vpn protocol from file

        Args:
            filename (string): path to certificate
        """
        vpn_protocol = False

        if not isinstance(filename, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(filename))
            )
        elif not filename.strip():
            raise ValueError(
                "The provided argument \"filename\" is empty"
            )

        if not os.path.isfile(filename):
            raise FileNotFoundError(
                "The provided file \"{}\"".format(filename)
                + "could not be found"
            )

        with open(filename, "r") as f:
            try:
                vpn_protocol = re.search(
                    r"proto\W(udp|tcp)", f.read()
                ).group(1)
            except AttributeError:
                pass
            except FileNotFoundError as e:
                raise exceptions.ImportConnectionError(e)

        return vpn_protocol

    def get_protocol_implementation_type(self, vpn_protocol):
        """Find and return protocol implementation type"""
        for plugin_name, protocol_types in SUPPORTED_PROTOCOLS.items():
            if vpn_protocol in protocol_types:
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
