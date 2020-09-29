import os

import gi
import pytest

gi.require_version("NM", "1.0")
from gi.repository import NM

from common import (
    CERT_FOLDER, ENV_CI_NAME, PLUGIN_CERT_FOLDER,
    CertificateManager, ConnectionManager, UserManager,
    exceptions
)

os.environ[ENV_CI_NAME] = "true"


class TestUnitConnectionManager:
    cm = ConnectionManager()

    def test_wrong_device_type(self):
        with pytest.raises(exceptions.IllegalVirtualDevice):
            self.cm.extract_virtual_device_type(
                os.path.join(CERT_FOLDER, "ProtonVPN_wrong_dev_type.ovpn")
            )

    def test_missing_device_type(self):
        with pytest.raises(exceptions.VirtualDeviceNotFound):
            self.cm.extract_virtual_device_type(
                os.path.join(CERT_FOLDER, "ProtonVPN_missing_dev_type.ovpn")
            )


class TestIntegrationConnectionManager():
    cm = ConnectionManager(
        virtual_device_name="testTunnel0"
    )
    um = UserManager()
    user = os.environ["vpntest_user"]
    pwd = os.environ["vpntest_pwd"]
    um.keyring_service = "TestConnectionManager"
    um.keyring_username = "TestAuthData"
    um.login(user, pwd)
    random_domain = "random.domain.to.add"

    @pytest.fixture
    def test_keyring_service(self):
        return "TestConnectionManager"

    @pytest.fixture
    def test_keyring_username(self):
        return "TestAuthData"

    def test_add_correct_connection(self):
        self.cm.add_connection(
            os.path.join(PLUGIN_CERT_FOLDER, "TestProtonVPN.ovpn"),
            self.user,
            self.pwd,
            CertificateManager.delete_cached_certificate,
            self.random_domain
        )
        assert isinstance(
            self.cm.get_proton_connection("all_connections")[0],
            NM.RemoteConnection
        )

    def test_add_missing_path_connection(self):
        with pytest.raises(FileNotFoundError):
            self.cm.add_connection(
                os.path.join(CERT_FOLDER, ""),
                self.user,
                self.pwd,
                CertificateManager.delete_cached_certificate,
                self.random_domain
            )

    @pytest.mark.parametrize(
        "user,pwd,excp",
        [
            ("", "test", ValueError), ("test", "", ValueError),
            (None, "test", TypeError), ([5], "test", TypeError),
        ]
    )
    def test_add_missing_cred_connection(self, user, pwd, excp):
        with pytest.raises(excp):
            self.cm.add_connection(
                os.path.join(CERT_FOLDER, "TestProtonVPN.ovpn"),
                user,
                pwd,
                CertificateManager.delete_cached_certificate,
                self.random_domain
            )

    def test_add_missing_method_connection(self):
        with pytest.raises(NotImplementedError):
            self.cm.add_connection(
                os.path.join(CERT_FOLDER, "TestProtonVPN.ovpn"),
                self.user,
                self.pwd,
                "",
                self.random_domain
            )

    def test_remove_correct_connection(self):
        self.cm.remove_connection()

    def test_remove_inexistent_connection(self):
        with pytest.raises(exceptions.ConnectionNotFound):
            self.cm.remove_connection()

    um.logout()
