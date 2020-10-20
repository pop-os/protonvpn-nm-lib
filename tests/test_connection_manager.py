import os

import gi
import pytest

gi.require_version("NM", "1.0")
from gi.repository import NM

from common import (CERT_FOLDER, ENV_CI_NAME, PLUGIN_CERT_FOLDER,
                    CertificateManager, ConnectionManager, KillSwitchManager,
                    UserManager, IPv6LeakProtectionManager,
                    KillswitchStatusEnum, UserSettingStatusEnum, exceptions)

USER_CONFIGURATIONS = {
    "connection": {
        "default_protocol": "tcp",
        "killswitch": 1,
        "dns": {
            "status": 2,
            "custom_dns": "10.18.0.1"
        },
        "split_tunneling": {
            "status": 0,
            "ip_list": []
        }
    },
    "general": {},
    "advanced": {},
    "tray": {}
}
os.environ[ENV_CI_NAME] = "true"


class FakeUserConfigurationManager():
    @property
    def killswitch(self):
        return KillswitchStatusEnum.DISABLED

    @property
    def dns(self):
        return (UserSettingStatusEnum.DISABLED, [])


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
    fake_user_conf_manager = FakeUserConfigurationManager()
    ks_manager = KillSwitchManager(
        fake_user_conf_manager,
        ks_conn_name="testks",
        ks_interface_name="testksintrf0",
        routed_conn_name="testroutedks",
        routed_interface_name="testroutedks0",
    )
    ipv6_lp_manager = IPv6LeakProtectionManager(
        conn_name="test-ipv6-leak-prot",
        iface_name="testipv6intrf0",
    )
    um = UserManager()
    user = os.environ["vpntest_user"]
    pwd = os.environ["vpntest_pwd"]
    um.keyring_service = "TestConnectionManager"
    um.keyring_username = "TestSessionData"
    um.login(user, pwd)
    random_domain = "random.domain.to.add"

    @pytest.fixture
    def test_keyring_service(self):
        return "TestConnectionManager"

    @pytest.fixture
    def test_keyring_username(self):
        return "TestSessionData"

    def test_add_correct_connection(self):
        self.cm.add_connection(
            os.path.join(PLUGIN_CERT_FOLDER, "TestProtonVPN.ovpn"),
            self.user,
            self.pwd,
            CertificateManager.delete_cached_certificate,
            self.random_domain,
            self.fake_user_conf_manager,
            self.ks_manager,
            self.ipv6_lp_manager,
            "192.168.0.1"
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
                self.random_domain,
                self.fake_user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                "192.168.0.1"
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
                self.random_domain,
                self.fake_user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                "192.168.0.1"
            )

    def test_add_missing_method_connection(self):
        with pytest.raises(NotImplementedError):
            self.cm.add_connection(
                os.path.join(CERT_FOLDER, "TestProtonVPN.ovpn"),
                self.user,
                self.pwd,
                "",
                self.random_domain,
                self.fake_user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager,
                "192.168.0.1"
            )

    def test_remove_correct_connection(self):
        self.cm.remove_connection(
            self.fake_user_conf_manager,
            self.ks_manager,
            self.ipv6_lp_manager
        )

    def test_remove_inexistent_connection(self):
        with pytest.raises(exceptions.ConnectionNotFound):
            self.cm.remove_connection(
                self.fake_user_conf_manager,
                self.ks_manager,
                self.ipv6_lp_manager
            )

    um.logout([], [])
