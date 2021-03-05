import os

import gi
import pytest

gi.require_version("NM", "1.0")
from gi.repository import NM

from common import (CERT_FOLDER, ENV_CI_NAME, MOCK_SESSIONDATA,
                    PLUGIN_CERT_FOLDER, PWD, Certificate, ConnectionManager,
                    ConnectionMetadata, IPv6LeakProtection, KillSwitch,
                    KillswitchStatusEnum, NetworkManagerConnectionTypeEnum,
                    ProtocolEnum, ReconnectorManager, UserConfigurationManager,
                    UserManager, UserSettingStatusEnum, exceptions)

TEST_KEYRING_SERVICE = "TestConnManager"
TEST_KEYRING_SESSIONDATA = "TestConnManSessionData"
TEST_KEYRING_USERDATA = "TestConnManUserData"
TEST_KEYRING_PROTON_USER = "TestConnManUser"

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

test_user_config_dir = os.path.join(PWD, "test_config_protonvpn")
test_user_config_fp = os.path.join(
    test_user_config_dir, "test_user_configurations.json"
)
ucm = UserConfigurationManager(
    user_config_dir=test_user_config_dir,
    user_config_fp=test_user_config_fp
)


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
    @classmethod
    def setup_class(cls):
        connection_metadata = ConnectionMetadata()
        um = UserManager(user_conf_manager=ucm)
        connection_metadata.save_servername("TESTCONNMANAGER#1")
        connection_metadata.save_protocol(ProtocolEnum.TCP)
        um.keyring_service = TEST_KEYRING_SERVICE
        um.keyring_sessiondata = TEST_KEYRING_SESSIONDATA
        um.keyring_userdata = TEST_KEYRING_USERDATA
        um.keyring_proton_user = TEST_KEYRING_PROTON_USER
        um.store_data(
            data=MOCK_SESSIONDATA,
            keyring_username=TEST_KEYRING_SESSIONDATA,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=False
        )
        um.store_data(
            data=dict(
                VPN=dict(
                    Name="test_username",
                    Password="test_password",
                    MaxTier="2",
                )
            ),
            keyring_username=TEST_KEYRING_USERDATA,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=True
        )
        um.store_data(
            data={"test_proton_username": "test_server_man_user"},
            keyring_username=TEST_KEYRING_PROTON_USER,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=False
        )

    @classmethod
    def teardown_class(cls):
        um = UserManager(user_conf_manager=ucm)
        um.keyring_service = TEST_KEYRING_SERVICE
        um.keyring_sessiondata = TEST_KEYRING_SESSIONDATA
        um.keyring_userdata = TEST_KEYRING_USERDATA
        um.keyring_proton_user = TEST_KEYRING_PROTON_USER
        um.delete_stored_data(TEST_KEYRING_PROTON_USER, TEST_KEYRING_SERVICE)
        um.delete_stored_data(TEST_KEYRING_SESSIONDATA, TEST_KEYRING_SERVICE)
        um.delete_stored_data(TEST_KEYRING_USERDATA, TEST_KEYRING_SERVICE)

    @pytest.fixture
    def openvpn_user(self):
        return "test_username"

    @pytest.fixture
    def openvpn_pass(self):
        return "test_password"

    @pytest.fixture
    def conn_man(self):
        return ConnectionManager(
            virtual_device_name="testTunnel0"
        )

    @pytest.fixture
    def fake_user_conf_man(self):
        return FakeUserConfigurationManager()

    @pytest.fixture
    def reconnector_manager(self):
        return ReconnectorManager()

    @pytest.fixture
    def ks_man(self, fake_user_conf_man):
        return KillSwitch(
            fake_user_conf_man,
            ks_conn_name="testks",
            ks_interface_name="testksintrf0",
            routed_conn_name="testroutedks",
            routed_interface_name="testroutedks0",
        )

    @pytest.fixture
    def ipv6_lp_man(self):
        return IPv6LeakProtection(
            conn_name="test-ipv6-leak-prot",
            iface_name="testipv6intrf0",
        )

    @pytest.fixture
    def random_domain(self):
        return "random.domain.to.add"

    def test_add_correct_connection(
        self, conn_man, openvpn_user, openvpn_pass, random_domain,
        fake_user_conf_man, ks_man, ipv6_lp_man
    ):
        conn_man.add_connection(
            os.path.join(PLUGIN_CERT_FOLDER, "TestProtonVPN.ovpn"),
            openvpn_user,
            openvpn_pass,
            Certificate.delete_cached_certificate,
            random_domain,
            fake_user_conf_man,
            ks_man,
            ipv6_lp_man,
            "192.168.0.1"
        )
        assert isinstance(
            conn_man.get_protonvpn_connection(
                NetworkManagerConnectionTypeEnum.ALL
            )[0],
            NM.RemoteConnection
        )

    def test_add_missing_path_connection(
        self, conn_man, openvpn_user, openvpn_pass, random_domain,
        fake_user_conf_man, ks_man, ipv6_lp_man
    ):
        with pytest.raises(FileNotFoundError):
            conn_man.add_connection(
                os.path.join(CERT_FOLDER, ""),
                openvpn_user,
                openvpn_pass,
                Certificate.delete_cached_certificate,
                random_domain,
                fake_user_conf_man,
                ks_man,
                ipv6_lp_man,
                "192.168.0.1"
            )

    @pytest.mark.parametrize(
        "user,pwd,excp",
        [
            ("", "test", ValueError), ("test", "", ValueError),
            (None, "test", TypeError), ([5], "test", TypeError),
        ]
    )
    def test_add_missing_cred_connection(
        self, conn_man, user, pwd, excp, random_domain,
        fake_user_conf_man, ks_man, ipv6_lp_man

    ):
        with pytest.raises(excp):
            conn_man.add_connection(
                os.path.join(CERT_FOLDER, "TestProtonVPN.ovpn"),
                user,
                pwd,
                Certificate.delete_cached_certificate,
                random_domain,
                fake_user_conf_man,
                ks_man,
                ipv6_lp_man,
                "192.168.0.1"
            )

    def test_add_missing_method_connection(
        self, conn_man, openvpn_user, openvpn_pass, random_domain,
        fake_user_conf_man, ks_man, ipv6_lp_man
    ):
        with pytest.raises(FileNotFoundError):
            conn_man.add_connection(
                os.path.join(CERT_FOLDER, "TestProtonVPN.ovpn"),
                openvpn_user,
                openvpn_pass,
                "",
                random_domain,
                fake_user_conf_man,
                ks_man,
                ipv6_lp_man,
                "192.168.0.1"
            )

    def test_remove_correct_connection(
        self, conn_man, fake_user_conf_man,
        ks_man, ipv6_lp_man, reconnector_manager
    ):
        conn_man.remove_connection(
            fake_user_conf_man,
            ks_man,
            ipv6_lp_man,
            reconnector_manager
        )

    def test_remove_inexistent_connection(
        self, conn_man, fake_user_conf_man,
        ks_man, ipv6_lp_man, reconnector_manager
    ):
        with pytest.raises(exceptions.ConnectionNotFound):
            conn_man.remove_connection(
                fake_user_conf_man,
                ks_man,
                ipv6_lp_man,
                reconnector_manager
            )
