import pytest

from common import (MOCK_SESSIONDATA, ProtonSessionWrapper, UserSession,
                    exceptions)

TEST_KEYRING = dict(
    sname=["test1", "test2", "test3"],
    uname=["test1_user", "test2_user", "test3_user"]
)


class TestUserSession:

    usm = UserSession()

    @pytest.fixture
    def test_keyring_service(self):
        return "TestUserSession"

    @pytest.fixture
    def test_keyring_username_sessiondata(self):
        return "TestSessionData"

    @pytest.fixture
    def test_keyring_username_userdata(self):
        return "TestUserData"

    @pytest.mark.parametrize(
        "unexpected_session_data,exception",
        [
            ("", exceptions.IllegalData),
            ({}, exceptions.IllegalData),
            (None, exceptions.IllegalData)
        ]
    )
    def test_unxexpected_store_user_session(
        self,
        unexpected_session_data,
        exception,
        test_keyring_service,
        test_keyring_username_sessiondata
    ):
        with pytest.raises(exception):
            self.usm.store_data(
                unexpected_session_data,
                test_keyring_username_sessiondata,
                test_keyring_service
            )

    @pytest.mark.parametrize(
        "session_data,expected_servicename,expected_username",
        [
            (
                MOCK_SESSIONDATA,
                TEST_KEYRING["sname"][0],
                TEST_KEYRING["uname"][0]
            ),
            (
                MOCK_SESSIONDATA,
                TEST_KEYRING["sname"][1],
                TEST_KEYRING["uname"][0]
            ),
            (
                MOCK_SESSIONDATA,
                TEST_KEYRING["sname"][2],
                TEST_KEYRING["uname"][0]
            )
        ]
    )
    def test_store_expected_session(
        self,
        session_data,
        expected_servicename,
        expected_username,
    ):
        self.usm.store_data(
            data=session_data,
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
        self.usm.get_stored_data(
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
            ProtonSessionWrapper
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
        self.usm.delete_stored_data(
            keyring_service=expected_servicename,
            keyring_username=expected_username
        )
