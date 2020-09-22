import os

import pytest
from proton.api import Session

from lib import exceptions
from lib.services.user_manager import UserManager
from lib.enums import ClientSuffixEnum


class TestUnitUserManager():
    um = UserManager()

    @pytest.fixture
    def pvpn_user(self):
        user = os.environ["vpntest_user"]
        return user

    @pytest.fixture
    def pvpn_pass(self):
        pwd = os.environ["vpntest_pwd"]
        return pwd

    @pytest.fixture
    def test_keyring_service(self):
        return "TestUserManager"

    @pytest.fixture
    def test_keyring_username(self):
        return "TestAuthData"

    def test_correct_login(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        self.um.login(pvpn_user, pvpn_pass)

    def test_missing_username_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        with pytest.raises(ValueError):
            self.um.login("", pvpn_pass)

    def test_missing_password_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        with pytest.raises(ValueError):
            self.um.login(pvpn_user, "")

    def test_int_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        with pytest.raises(TypeError):
            self.um.login(5, 5)

    def test_empty_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        with pytest.raises(ValueError):
            self.um.login("", "")

    def test_load_existing_session(
        self, test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        assert isinstance(
            self.um.load_session(),
            Session
        )

    def test_load_no_session(self):
        self.um.keyring_service = "Example"
        self.um.keyring_username = "Session"
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.load_session()

    def test_load_missing_session(self):
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.keyring_service = ""
            self.um.keyring_username = ""
            self.um.load_session()

    def test_fetch_correct_vpn_cred(
        self, test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        user = os.environ["openvpntest_user"]
        pwd = os.environ["openvpntest_pwd"]
        (resp_user, resp_pwd) = self.um.fetch_vpn_credentials()
        assert (resp_user, resp_pwd) == (
            user + "+" + ClientSuffixEnum.PLATFORM, pwd
        )

    def test_fetch_incorrect_service_vpn_cred(
        self, test_keyring_username
    ):
        self.um.keyring_service = "Example"
        self.um.keyring_username = test_keyring_username
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.fetch_vpn_credentials()

    def test_correct_logout(
        self, test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_username = test_keyring_username
        self.um.logout()
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.load_session()

    def test_incorrect_logout(
        self, test_keyring_service, test_keyring_username
    ):
        self.um.keyring_service = ""
        self.um.keyring_username = test_keyring_username
        with pytest.raises(exceptions.StoredSessionNotFound):
            self.um.logout()
