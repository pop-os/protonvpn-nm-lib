import os

import pytest

from common import (ClientSuffixEnum, ProtonSessionWrapper, UserManager,
                    exceptions)


class TestUnitUserManager():
    um = UserManager()

    @classmethod
    def setup_class(cls):
        um = UserManager()
        um.store_data(
            dict(
                VPN=dict(
                    Name="test_username",
                    Password="test_password",
                    MaxTier="2",
                )
            ),
            "TestUserData",
            "TestUserManager",
            True
        )

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
    def test_keyring_username_sessiondata(self):
        return "TestSessionData"

    @pytest.fixture
    def test_keyring_username_userdata(self):
        return "TestUserData"

    @pytest.fixture
    def test_keyring_username_proton_username(self):
        return "TestProtonUsername"

    def test_correct_login(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_sessiondata = test_keyring_username_sessiondata
        self.um.login(pvpn_user, pvpn_pass)

    def test_missing_username_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_keyring_service, test_keyring_username_sessiondata
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
        self, test_keyring_service, test_keyring_username_userdata
    ):
        self.um.keyring_service = test_keyring_service
        self.um.keyring_userdata = test_keyring_username_userdata
        user = "test_username"
        pwd = "test_password"
        (resp_user, resp_pwd) = self.um.get_stored_vpn_credentials()
        assert (resp_user, resp_pwd) == (
            user + "+" + ClientSuffixEnum.PLATFORM, pwd
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
