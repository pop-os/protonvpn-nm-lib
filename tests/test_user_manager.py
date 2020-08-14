from lib.services.user_manager import UserManager
from lib.services.user_manager import UserSessionManager
from lib import exceptions
import pytest
import os


class TestUserManager():
    cm = UserManager()

    @pytest.fixture
    def pvpn_user(self):
        user = os.environ["vpntest_user"]
        return user

    @pytest.fixture
    def pvpn_pass(self):
        pwd = os.environ["vpntest_pwd"]
        return pwd
