from lib.services.plugin_manager import PluginManager
from lib import exceptions
import pytest
import gi
gi.require_version("NM", "1.0")
from gi.repository import NM
import os

PWD = os.path.dirname(os.path.abspath(__file__))
CERT_FOLDER = os.path.join(PWD, "certificates")


class TestUnitPluginManager:
    pm = PluginManager()

    def test_correct_tcp_implementation(self):
        assert self.pm.get_protocol_implementation_type("tcp") == "openvpn"

    def test_correct_udp_implementation(self):
        assert self.pm.get_protocol_implementation_type("udp") == "openvpn"

    def test_incorrect_openvpn_protocol(self):
        with pytest.raises(exceptions.IllegalVPNProtocol):
            self.pm.get_protocol_implementation_type("ikve2")

    def test_random_protocol(self):
        with pytest.raises(exceptions.IllegalVPNProtocol):
            self.pm.get_protocol_implementation_type("some_protocol")

    def test_incorrect_plugin_protocol_name(self):
        with pytest.raises(exceptions.ProtocolPluginNotFound):
            self.pm.get_matching_plugin("ikve2")

    def test_correct_plugin_protocol_name(self):
        assert isinstance(
            self.pm.get_matching_plugin("openvpn"),
            NM.VpnEditorPlugin
        )


class TestIntegrationPluginManager:
    pm = PluginManager()

    def test_correct_import(self):
        assert isinstance(
            self.pm.import_connection_from_file(
                os.path.join(CERT_FOLDER, "ProtonVPN.ovpn")
            ),
            NM.SimpleConnection
        )

    def test_broken_import(self):
        with pytest.raises(exceptions.ImportConnectionError):
            self.pm.import_connection_from_file(
                os.path.join(CERT_FOLDER, "ProtonVPN_broken_cert.ovpn")
            )

    def test_missing_import(self):
        with pytest.raises(FileNotFoundError):
            self.pm.import_connection_from_file(
                os.path.join(CERT_FOLDER, "")
            )

    def test_filename_is_random(self):
        with pytest.raises(FileNotFoundError):
            self.pm.import_connection_from_file(
                os.path.join(CERT_FOLDER, "someradnom_STRING")
            )

    def test_filename_is_int(self):
        with pytest.raises(TypeError):
            self.pm.import_connection_from_file(
                os.path.join(CERT_FOLDER, 25)
            )

    def test_import_from_subfolder(self):
        with pytest.raises(FileNotFoundError):
            self.pm.import_connection_from_file(
                os.path.join(CERT_FOLDER, "./random_folder/ProtonVPN.ovpn")
            )
