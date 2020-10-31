
import pytest
from common import ProtonSessionWrapper, UserManager, exceptions, ProtonSessionAPIMethodEnum
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


class TestProtonSessionWrapperAPIRequest():
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

    @pytest.mark.parametrize(
        "error", [
            400, 404, 409, 422, 500, 501
        ]
    )
    def test_expected_unhandled_requests(
        self, mock_api_request,
        api_tokens, error
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            ),
            api_tokens,
            "end_mock"
        ]
        with pytest.raises(exceptions.APIError):
            session.api_request("/vpn")

    @pytest.mark.parametrize(
        "error", [
            000, "as", 12543, False
        ]
    )
    def test_unexpected_unhandled_requests(
        self, mock_api_request,
        api_tokens, error
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            ),
            api_tokens,
            "end_mock"
        ]
        with pytest.raises(exceptions.UnhandledAPIError):
            session.api_request("/vpn")

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

    def test_expected_api_429(
        self, mock_api_request,
        api_tokens
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": 429,
                    "Error": "Error code 403",
                    "Headers": {"Retry-After": 0.5}
                },
            ),
            ProtonError(
                {
                    "Code": 404,
                    "Error": "Error code 404",
                },
            ),
        ]
        with pytest.raises(exceptions.APIError):
            session.api_request("/vpn")

    def test_expected_api_503(
        self, mock_api_request,
        api_tokens
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": 503,
                    "Error": "Error code 503",
                },
            ),
            ProtonError(
                {
                    "Code": 404,
                    "Error": "Error code 404",
                },
            ),
        ]
        with pytest.raises(exceptions.APIError):
            session.api_request("/vpn")

    def test_expected_api_5002(self, mock_api_request):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": 5002,
                    "Error": "Error code 5002",
                },
            ),
        ]
        with pytest.raises(exceptions.API5002Error):
            session.api_request("/vpn")

    def test_expected_api_5003(self, mock_api_request):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": 5003,
                    "Error": "Error code 5003",
                },
            ),
        ]
        with pytest.raises(exceptions.API5003Error):
            session.api_request("/vpn")


class TestProtonSessionWrapperAuthenticate():
    @pytest.fixture
    def mock_authenticate_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.authenticate"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    def test_api_200(self, mock_authenticate_request):
        mock_authenticate_request.return_value.status_code = 200
        session.authenticate("username", "password")

    @pytest.mark.parametrize(
        "error", [
            400, 404, 409, 422, 500, 501
        ]
    )
    def test_expected_unhandled_requests(
        self, mock_authenticate_request, error
    ):
        mock_authenticate_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            )
        ]
        with pytest.raises(exceptions.APIError):
            session.authenticate("username", "password")

    @pytest.mark.parametrize(
        "error", [
            000, "as", 12543, False
        ]
    )
    def test_unexpected_unhandled_requests(
        self, mock_authenticate_request, error
    ):
        mock_authenticate_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            )
        ]
        with pytest.raises(exceptions.UnhandledAPIError):
            session.authenticate("username", "password")

    def test_expected_api_429(self, mock_authenticate_request):
        mock_authenticate_request.side_effect = [
            ProtonError(
                {
                    "Code": 429,
                    "Error": "Error code 403",
                    "Headers": {"Retry-After": 0.5}
                },
            ),
            ProtonError(
                {
                    "Code": 404,
                    "Error": "Error code 404",
                },
            ),
        ]
        with pytest.raises(exceptions.APIError):
            session.authenticate("username", "password")

    def test_expected_api_503(self, mock_authenticate_request):
        mock_authenticate_request.side_effect = [
            ProtonError(
                {
                    "Code": 503,
                    "Error": "Error code 503",
                },
            ),
            ProtonError(
                {
                    "Code": 404,
                    "Error": "Error code 404",
                },
            ),
        ]
        with pytest.raises(exceptions.APIError):
            session.authenticate("username", "password")

    def test_expected_api_5002(self, mock_authenticate_request):
        mock_authenticate_request.side_effect = [
            ProtonError(
                {
                    "Code": 5002,
                    "Error": "Error code 5002",
                },
            ),
        ]
        with pytest.raises(exceptions.API5002Error):
            session.authenticate("username", "password")

    def test_expected_api_5003(self, mock_authenticate_request):
        mock_authenticate_request.side_effect = [
            ProtonError(
                {
                    "Code": 5003,
                    "Error": "Error code 5003",
                },
            ),
        ]
        with pytest.raises(exceptions.API5003Error):
            session.authenticate("username", "password")


class TestProtonSessionWrapperLogout():
    @pytest.fixture
    def mock_logout_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.logout"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    def test_api_200(self, mock_logout_request):
        mock_logout_request.return_value.status_code = 200
        session.logout()

    @pytest.mark.parametrize(
        "error", [
            400, 404, 409, 422, 500, 501
        ]
    )
    def test_expected_unhandled_requests(
        self, mock_logout_request, error
    ):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            )
        ]
        with pytest.raises(exceptions.APIError):
            session.logout()

    @pytest.mark.parametrize(
        "error", [
            000, "as", 12543, False
        ]
    )
    def test_unexpected_unhandled_requests(
        self, mock_logout_request, error
    ):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            )
        ]
        with pytest.raises(exceptions.UnhandledAPIError):
            session.logout()

    def test_expected_api_403(self, mock_logout_request):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": 403,
                    "Error": "Error code 403"
                }
            )
        ]
        with pytest.raises(exceptions.API403Error):
            session.logout()

    def test_expected_api_429(self, mock_logout_request):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": 429,
                    "Error": "Error code 403",
                    "Headers": {"Retry-After": 0.5}
                },
            ),
            ProtonError(
                {
                    "Code": 404,
                    "Error": "Error code 404",
                },
            ),
        ]
        with pytest.raises(exceptions.APIError):
            session.logout()

    def test_expected_api_503(self, mock_logout_request):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": 503,
                    "Error": "Error code 503",
                },
            ),
            ProtonError(
                {
                    "Code": 404,
                    "Error": "Error code 404",
                },
            ),
        ]
        with pytest.raises(exceptions.APIError):
            session.logout()

    def test_expected_api_5002(self, mock_logout_request):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": 5002,
                    "Error": "Error code 5002",
                },
            ),
        ]
        with pytest.raises(exceptions.API5002Error):
            session.logout()

    def test_expected_api_5003(self, mock_logout_request):
        mock_logout_request.side_effect = [
            ProtonError(
                {
                    "Code": 5003,
                    "Error": "Error code 5003",
                },
            ),
        ]
        with pytest.raises(exceptions.API5003Error):
            session.logout()


class TestUnits():
    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.fixture
    def mock_authenticate_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.authenticate"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.fixture
    def mock_logout_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.logout"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.mark.parametrize(
        "method", [
            ProtonSessionAPIMethodEnum.API_REQUEST,
            ProtonSessionAPIMethodEnum.AUTHENTICATE,
            ProtonSessionAPIMethodEnum.LOGOUT,
        ]
    )
    def test_expected_method_exists(self, method):
        session.check_method_exists(method)

    @pytest.mark.parametrize(
        "method", [
            False,
            2014,
            2017,
            "test"
        ]
    )
    def test_unexpected_method_exists(self, method):
        with pytest.raises(exceptions.UnhandledAPIMethod):
            session.check_method_exists(method)
