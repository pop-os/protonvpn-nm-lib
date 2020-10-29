
import pytest
from common import ProtonSessionWrapper, UserManager, exceptions
from unittest.mock import patch
from proton import ProtonError

TEST_KEYRING_SERVICE = "TestServerManager"
TEST_KEYRING_SESSIONDATA = "TestServerManSessionData"
TEST_KEYRING_USERDATA = "TestServerManUserData"
TEST_KEYRING_PROTON_USER = "TestServerManUser"

um = UserManager(
    keyring_service=TEST_KEYRING_SERVICE,
    keyring_sessiondata=TEST_KEYRING_SESSIONDATA,
    keyring_userdata=TEST_KEYRING_USERDATA,
    keyring_proton_user=TEST_KEYRING_PROTON_USER
)

session = ProtonSessionWrapper(
    api_url="https://localhost",
    appversion="TestProtonSessionWrapper",
    user_agent="TestProtonSessionWrapper",
    TLSPinning=False,
    user_manager=um
)


class TestProtonSessionWrapper():

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.fixture
    def api_tokens(self):
        yield {
            "AccessToken": "test_access_token",
            "RefreshToken": "test_refresh_token"
        }

    @pytest.fixture
    def missing_api_tokens(self):
        yield {
            "_missing_access_token": "test_access_token",
            "_missing_refresh_token": "test_refresh_token"
        }

    @pytest.fixture
    def proton_error_401(self):
        yield ProtonError(
            {
                "Code": 401,
                "Error": "Error code 401"
            }
        )

    def test_api_200(self, mock_api_request):
        mock_api_request.return_value.status_code = 200
        resp = session.api_request("/vpn")
        assert resp.status_code == 200

    def test_expected_api_401(
        self, mock_api_request,
        proton_error_401, api_tokens
    ):
        mock_api_request.side_effect = [
            proton_error_401,
            api_tokens,
            "end_mock"
        ]
        session.api_request("/vpn")

    def test_unexpected_api_401(
        self, mock_api_request,
        proton_error_401, missing_api_tokens
    ):
        mock_api_request.side_effect = [
            proton_error_401,
            missing_api_tokens,
            "end_mock"
        ]
        with pytest.raises(exceptions.UnhandledAPIError):
            session.api_request("/vpn")

    def test_expected_api_403(
        self, mock_api_request,
        api_tokens
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": 403,
                    "Error": "Error code 403"
                }
            ),
            api_tokens,
            "end_mock"
        ]
        with pytest.raises(exceptions.API403Error):
            session.api_request("/vpn")
