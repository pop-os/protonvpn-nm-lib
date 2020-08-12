from lib import exceptions
import pytest
from lib.services.user_session_manager import UserSessionManager
from proton.api import Session

MOCK_AUTHDATA = {
    "api_url": "https://api.protonvpn.ch/tests/ping",
    "appversion": "4",
    "cookies": {
        "Session-Id": "session_id",
        "Version": "default"
    },
    "session_data": {
        "UID": "some_UID",
        "AccessToken": "some_AccessToken",
        "RefreshToken": "some_RefreshToken",
        "Scope": [
            "full",
            "self",
            "payments",
            "keys",
            "parent",
            "paid",
            "nondelinquent",
            "mail",
            "vpn",
            "calendar"
        ]
    }
}

TEST_KEYRING = dict(
    sname=["test1", "test2", "test3"],
    uname=["test1_user", "test2_user", "test3_user"] 
)


class TestUserSessionManager:

    usm = UserSessionManager()

    @pytest.mark.parametrize(
        "unexpected_auth_data,exception",
        [
            ("", exceptions.IllegalAuthData),
            ({}, exceptions.IllegalAuthData),
            (None, exceptions.IllegalAuthData)
        ]
    )
    def test_unxexpected_store_user_session(
        self,
        unexpected_auth_data,
        exception
    ):
        with pytest.raises(exception):
            self.usm.store_user_session(unexpected_auth_data)

    @pytest.mark.parametrize(
        "auth_data,expected_servicename,expected_username",
        [
            (MOCK_AUTHDATA, TEST_KEYRING["sname"][0], TEST_KEYRING["uname"][0]),
            (MOCK_AUTHDATA, TEST_KEYRING["sname"][1], TEST_KEYRING["uname"][0]),
            (MOCK_AUTHDATA, TEST_KEYRING["sname"][2], TEST_KEYRING["uname"][0])
        ]
    )
    def test_store_expected_session(
        self,
        auth_data,
        expected_servicename,
        expected_username,
    ):
        self.usm.store_user_session(
            auth_data=auth_data,
            keyring_service=expected_servicename,
            keyring_username=expected_username
        )

    @pytest.mark.parametrize(
        "expected_servicename,expected_username",
        [
            (TEST_KEYRING["sname"][0], TEST_KEYRING["uname"][0]),
            (TEST_KEYRING["sname"][1], TEST_KEYRING["uname"][0]),
            (TEST_KEYRING["sname"][2], TEST_KEYRING["uname"][0])
        ]
    )
    def test_get_expected_stored_session(
        self,
        expected_servicename,
        expected_username,
    ):
        self.usm.get_stored_user_session(
            keyring_service=expected_servicename,
            keyring_username=expected_username
        )

    @pytest.mark.parametrize(
        "expected_servicename,expected_username",
        [
            (TEST_KEYRING["sname"][0], TEST_KEYRING["uname"][0]),
            (TEST_KEYRING["sname"][1], TEST_KEYRING["uname"][0]),
            (TEST_KEYRING["sname"][2], TEST_KEYRING["uname"][0])
        ]
    )
    def test_load_expected_stored_session(
        self,
        expected_servicename,
        expected_username,
    ):
        assert isinstance(
            self.usm.load_stored_user_session(
                keyring_service=expected_servicename,
                keyring_username=expected_username
            ),
            Session
        )

    @pytest.mark.parametrize(
        "expected_servicename,expected_username",
        [
            (TEST_KEYRING["sname"][0], TEST_KEYRING["uname"][0]),
            (TEST_KEYRING["sname"][1], TEST_KEYRING["uname"][0]),
            (TEST_KEYRING["sname"][2], TEST_KEYRING["uname"][0])
        ]
    )
    def test_delete_expected_stored_session(
        self,
        expected_servicename,
        expected_username,
    ):
        self.usm.delete_user_session(
            keyring_service=expected_servicename,
            keyring_username=expected_username
        )
