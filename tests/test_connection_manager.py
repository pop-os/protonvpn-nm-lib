from lib.services.connection_manager import ConnectionManager
from lib.services.plugin_manager import PluginManager
from lib import exceptions
import pytest
import os

PWD = os.path.dirname(os.path.abspath(__file__))
CERT_FOLDER = os.path.join(PWD, "certificates")


class TestConnectionManager:
    cm = ConnectionManager(PluginManager())

    def test_wrong_device_type(self):
        with pytest.raises(exceptions.IllegalVirtualDevice):
            self.cm.get_virtual_device_type(
                os.path.join(CERT_FOLDER, "ProtonVPN_wrong_dev_type.ovpn")
            )

    def test_missing_device_type(self):
        with pytest.raises(exceptions.VirtualDeviceNotFound):
            self.cm.get_virtual_device_type(
                os.path.join(CERT_FOLDER, "ProtonVPN_missing_dev_type.ovpn")
            )
