from lib.services.connection_manager import ConnectionManager
from lib.services.plugin_manager import PluginManager
from lib.services.user_manager import UserManager
from lib.services.certificate_manager import CertificateManager
from lib import exceptions
import pytest
import os

PWD = os.path.dirname(os.path.abspath(__file__))
CERT_FOLDER = os.path.join(PWD, "certificates")


class TestUnitConnectionManager:
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


class TestIntegrationConnectionManager():
    cm = ConnectionManager(PluginManager())
    um = UserManager()
    user = os.environ["vpntest_user"]
    pwd = os.environ["vpntest_pwd"]
    um.keyring_service = "TestConnectionManager"
    um.keyring_username = "TestAuthData"
    um.login(user, pwd)

    @pytest.fixture
    def test_keyring_service(self):
        return "TestConnectionManager"

    @pytest.fixture
    def test_keyring_username(self):
        return "TestAuthData"

    def test_add_expected_connection(self):
        self.cm.add_connection(
            os.path.join(CERT_FOLDER, "ProtonVPN.ovpn"),
            self.user,
            self.pwd,
            CertificateManager.delete_cached_certificate
        )
