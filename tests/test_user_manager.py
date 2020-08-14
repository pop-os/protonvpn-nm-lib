from lib.services.user_manager import UserManager
from lib import exceptions
import pytest
import os
from proton.api import Session


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
    def test_service(self):
        return "TestUserManager"

    @pytest.fixture
    def test_authdata(self):
        return "TestAuthData"

    def test_correct_login(
        self,
        pvpn_user, pvpn_pass,
        test_service, test_authdata
    ):
        self.um.login(pvpn_user, pvpn_pass, test_service, test_authdata)

    def test_missing_username_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_service, test_authdata
    ):
        with pytest.raises(ValueError):
            self.um.login("", pvpn_pass, test_service, test_authdata)

    def test_missing_password_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_service, test_authdata
    ):
        with pytest.raises(ValueError):
            self.um.login(pvpn_user, "", test_service, test_authdata)

    def test_int_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_service, test_authdata
    ):
        with pytest.raises(TypeError):
            self.um.login(5, 5, test_service, test_authdata)

    def test_empty_login_cred(
        self,
        pvpn_user, pvpn_pass,
        test_service, test_authdata
    ):
        with pytest.raises(ValueError):
            self.um.login("", "", test_service, test_authdata)

    def test_load_existing_session(
        self, test_service, test_authdata
    ):
        assert isinstance(
            self.um.load_stored_user_session(test_service, test_authdata),
            Session
        )

    def test_load_no_session(self):
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.load_stored_user_session("Example", "Session")

    def test_load_missing_session(self):
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.load_stored_user_session("", "")

    def test_fetch_correct_vpn_cred(
        self, test_service, test_authdata
    ):
        user = os.environ["openvpntest_user"]
        pwd = os.environ["openvpntest_pwd"]
        (resp_user, resp_pwd) = self.um.fetch_vpn_credentials(
            test_service, test_authdata
        )
        assert (resp_user, resp_pwd) == (user, pwd)

    def test_fetch_incorrect_service_vpn_cred(
        self, test_service, test_authdata
    ):
        with pytest.raises(exceptions.JSONAuthDataNoneError):
            self.um.fetch_vpn_credentials(
                "", test_authdata
            )
