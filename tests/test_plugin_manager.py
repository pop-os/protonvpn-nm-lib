import os

import gi
import pytest

gi.require_version("NM", "1.0")
from gi.repository import NM

from common import (PLUGIN_CERT_FOLDER, PluginManager, ProtocolEnum,
                    ProtocolImplementationEnum, exceptions)


class TestUnitPluginManager:
    pm = PluginManager()

    def test_correct_tcp_implementation(self):
        assert (
            self.pm.get_protocol_implementation_type(ProtocolEnum.TCP)
            == ProtocolImplementationEnum.OPENVPN
        )

    def test_correct_udp_implementation(self):
        assert (
            self.pm.get_protocol_implementation_type(ProtocolEnum.UDP)
            == ProtocolImplementationEnum.OPENVPN
        )

    def test_incorrect_openvpn_protocol(self):
        with pytest.raises(ValueError):
            self.pm.get_protocol_implementation_type("ikve2")

    def test_random_protocol(self):
        with pytest.raises(ValueError):
            self.pm.get_protocol_implementation_type("some_protocol")

    def test_correct_plugin_protocol_name(self):
        assert isinstance(
            self.pm.get_matching_plugin("openvpn"),
            NM.VpnEditorPlugin
        )

    def test_incorrect_plugin_protocol_name(self):
        with pytest.raises(ValueError):
            self.pm.get_matching_plugin("ikve2")

    def test_extract_correct_protocol(self):
        proto = self.pm.extract_openvpn_protocol(
            os.path.join(PLUGIN_CERT_FOLDER, "TestProtonVPN.ovpn")
        )
        assert proto == ProtocolEnum.TCP.value

    def test_extract_missing_protocol(self):
        vpn_proto = self.pm.extract_openvpn_protocol(
            os.path.join(PLUGIN_CERT_FOLDER, "ProtonVPN_no_proto.ovpn")
        )
        assert vpn_proto is False

    def test_extract_incorrect_path(self):
        with pytest.raises(FileNotFoundError):
            self.pm.extract_openvpn_protocol(
                os.path.join(PLUGIN_CERT_FOLDER, "random_file.ovpn")
            )

    def test_extract_empty_path(self):
        with pytest.raises(ValueError):
            self.pm.extract_openvpn_protocol("")


class TestIntegrationPluginManager:
    pm = PluginManager()

    def test_correct_import(self):
        assert isinstance(
            self.pm.import_connection_from_file(
                os.path.join(PLUGIN_CERT_FOLDER, "TestProtonVPN.ovpn")
            ),
            NM.SimpleConnection
        )

    def test_broken_import(self):
        with pytest.raises(exceptions.ImportConnectionError):
            self.pm.import_connection_from_file(
                os.path.join(PLUGIN_CERT_FOLDER, "ProtonVPN_broken_cert.ovpn")
            )

    def test_missing_remote_import(self):
        with pytest.raises(exceptions.ImportConnectionError):
            self.pm.import_connection_from_file(
                os.path.join(PLUGIN_CERT_FOLDER, "ProtonVPN_no_remote.ovpn")
            )

    def test_missing_import(self):
        with pytest.raises(FileNotFoundError):
            self.pm.import_connection_from_file(
                os.path.join(PLUGIN_CERT_FOLDER, "")
            )

    def test_filename_is_random(self):
        with pytest.raises(FileNotFoundError):
            self.pm.import_connection_from_file(
                os.path.join(PLUGIN_CERT_FOLDER, "someradnom_STRING")
            )

    def test_filename_is_int(self):
        with pytest.raises(TypeError):
            self.pm.import_connection_from_file(
                os.path.join(PLUGIN_CERT_FOLDER, 25)
            )

    def test_import_from_subfolder(self):
        with pytest.raises(FileNotFoundError):
            self.pm.import_connection_from_file(
                os.path.join(
                    PLUGIN_CERT_FOLDER, "./random_folder/TestProtonVPN.ovpn"
                )
            )
