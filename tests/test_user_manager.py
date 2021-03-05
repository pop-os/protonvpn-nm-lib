from unittest.mock import patch
import shutil
import pytest
import os

from common import (MOCK_SESSIONDATA, MOCK_USER_DATA, NetshieldStatusEnum,
                    ClientSuffixEnum, ProtonSessionWrapper,
                    UserConfigurationManager,
                    UserManager, PWD, exceptions)

TEST_KEYRING_SERVICE = "TestUserManager"
TEST_KEYRING_SESSIONDATA = "TestUserManSessionData"
TEST_KEYRING_USERDATA = "TestUserManUserData"
TEST_KEYRING_PROTON_USER = "TestUserManUser"

test_user_config_dir = os.path.join(PWD, "test_user_manager_config_protonvpn")
test_user_config_fp = os.path.join(
    test_user_config_dir, "test_user_manager_configurations.json"
)
ucm = UserConfigurationManager(
    user_config_dir=test_user_config_dir,
    user_config_fp=test_user_config_fp
)


class TestUnitUserManager():
    um = UserManager(user_conf_manager=ucm)

    @classmethod
    def setup_class(cls):
        um = UserManager(user_conf_manager=ucm)
        um.user_session.store_data(
            data=MOCK_SESSIONDATA,
            keyring_username=TEST_KEYRING_SESSIONDATA,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=False
        )
        um.user_session.store_data(
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
        um.user_session.store_data(
            data={"test_proton_username": "test_server_man_user"},
            keyring_username=TEST_KEYRING_PROTON_USER,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=False
        )

    @classmethod
    def teardown_class(cls):
        um = UserManager(user_conf_manager=ucm)
        um.user_session.delete_stored_data(TEST_KEYRING_PROTON_USER, TEST_KEYRING_SERVICE)
        shutil.rmtree(test_user_config_dir)

    @pytest.fixture
    def mock_authenticate(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.core.proton_session_wrapper."
            "Session.authenticate"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.core.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.fixture
    def pvpn_user(self):
        return "test_username"

    @pytest.fixture
    def pvpn_pass(self):
        return "test_password"

    @pytest.fixture
    def test_keyring_service(self):
        return TEST_KEYRING_SERVICE

    @pytest.fixture
    def test_keyring_username_sessiondata(self):
        return TEST_KEYRING_SESSIONDATA

    @pytest.fixture
    def test_keyring_username_userdata(self):
        return TEST_KEYRING_USERDATA

    @pytest.fixture
    def test_keyring_username_proton_username(self):
        return TEST_KEYRING_PROTON_USER

    def test_correct_login(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata,
        test_keyring_username_userdata,
        mock_api_request, mock_authenticate
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        self.um.keyring_userdata = test_keyring_username_userdata
        mock_authenticate.side_effect = [
            MOCK_SESSIONDATA,
        ]
        mock_api_request.side_effect = [
            MOCK_USER_DATA
        ]
        self.um.login(pvpn_user, pvpn_pass)

    def test_missing_username_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata,
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        with pytest.raises(ValueError):
            self.um.login("", pvpn_pass)

    def test_missing_password_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        with pytest.raises(ValueError):
            self.um.login(pvpn_user, "")

    def test_int_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        with pytest.raises(TypeError):
            self.um.login(5, 5)

    def test_empty_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        with pytest.raises(ValueError):
            self.um.login("", "")

    def test_load_existing_session(
        self, test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        assert isinstance(
            self.um.load_session(),
            ProtonSessionWrapper
        )

    def test_load_no_session(self):
        self.um.keyring_service = "Example"
        self.um.keyring_sessiondata = "Session"
        with pytest.raises(exceptions.JSONDataNoneError):
            self.um.load_session()

    def test_load_missing_session(self):
        with pytest.raises(exceptions.JSONDataNoneError):
            self.um.keyring_service = ""
            self.um.keyring_sessiondata = ""
            self.um.load_session()

    def test_get_stored_vpn_credentials(
        self, pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_userdata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_userdata = test_keyring_username_userdata
        (resp_user, resp_pwd) = self.um.get_stored_vpn_credentials()
        openvn_username = MOCK_USER_DATA["VPN"]["Name"]
        openvpn_password = MOCK_USER_DATA["VPN"]["Password"]
        assert (resp_user, resp_pwd) == (
            openvn_username
            + "+" + ClientSuffixEnum.PLATFORM.value
            + "+" + NetshieldStatusEnum.DISABLED.value,
            openvpn_password
        )

    def test_get_incorrect_stored_vpn_credentials(
        self, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = "Example"
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        with pytest.raises(exceptions.JSONDataNoneError):
            self.um.cache_user_data()

    def test_correct_logout(
        self, test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        self.um.logout([], [])
        with pytest.raises(exceptions.JSONDataNoneError):
            self.um.load_session()

    def test_incorrect_logout(
        self, test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = ""
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        with pytest.raises(exceptions.StoredProtonUsernameNotFound):
            self.um.logout([], [])
