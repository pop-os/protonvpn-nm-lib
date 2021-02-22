
import json
import os
from unittest.mock import patch

import pytest
from proton import ProtonError

from common import (PWD, RAW_LOADS_LIST, RAW_SERVER_LIST, MetadataEnum,
                    ProtonSessionAPIMethodEnum, ProtonSessionWrapper,
                    UserManager, UserConfigurationManager, exceptions)

TEST_KEYRING_SERVICE = "TestServerManager"
TEST_KEYRING_SESSIONDATA = "TestServerManSessionData"
TEST_KEYRING_USERDATA = "TestServerManUserData"
TEST_KEYRING_PROTON_USER = "TestServerManUser"

test_user_config_dir = os.path.join(PWD, "test_config_protonvpn")
test_user_config_fp = os.path.join(
    test_user_config_dir, "test_user_configurations.json"
)
ucm = UserConfigurationManager(
    user_config_dir=test_user_config_dir,
    user_config_fp=test_user_config_fp
)

um = UserManager(
    user_conf_manager=ucm,
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
conn_state_filepath = os.path.join(
    PWD, "test_proton_session_wrapper_conn_state_metadata.json"
)
last_conn_state_filepath = os.path.join(
    PWD, "test_proton_session_wrapper_last_conn_state_metadata.json"
)
server_cache_filepath = os.path.join(
    PWD, "test_proton_session_wrapper_server_cache_metadata.json"
)
TEST_CACHED_SERVERLIST = os.path.join(
    PWD, "test_proton_session_wrapper_server_cache.json"
)
session.METADATA_DICT = {
    MetadataEnum.CONNECTION: conn_state_filepath,
    MetadataEnum.LAST_CONNECTION: last_conn_state_filepath,
    MetadataEnum.SERVER_CACHE: server_cache_filepath
}
session.CACHED_SERVERLIST = TEST_CACHED_SERVERLIST
session.FULL_CACHE_TIME_EXPIRE = 1 / 240
session.LOADS_CACHE_TIME_EXPIRE = 1 / 240


class TestProtonSessionWrapperAPIRequest():
    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.core.proton_session_wrapper."
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
        with pytest.raises(AttributeError):
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
            "protonvpn_nm_lib.core.proton_session_wrapper."
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
            "protonvpn_nm_lib.core.proton_session_wrapper."
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


class TestProtonSessionWrapperFullCache():

    @classmethod
    def setup_class(cls):
        with open(conn_state_filepath, "w") as a:
            json.dump({
                "connected_server": "conn_test",
                "connected_protocol": "tcp",
                "connected_time": 0000000
            }, a)

        with open(last_conn_state_filepath, "w") as f:
            json.dump({
                "connected_server": "last_conn_test",
                "last_connect_ip": "192.168.0.1"
            }, f)

        with open(server_cache_filepath, "w") as c:
            json.dump({
                "full_cache_timestamp": "1606390288",
                "loads_cache_timestamp": "1606390288"
            }, c)

    @classmethod
    def teardown_class(cls):
        os.remove(conn_state_filepath)
        os.remove(last_conn_state_filepath)
        os.remove(server_cache_filepath)
        os.remove(TEST_CACHED_SERVERLIST)

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.core.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    def test_full_cache(self, mock_api_request):
        mock_api_request.side_effect = [
            RAW_SERVER_LIST
        ]
        session.full_cache()
        with open(TEST_CACHED_SERVERLIST) as f:
            file = json.load(f)

            assert file["LogicalServers"][0]["Name"] == "TEST#5"

    @pytest.mark.parametrize(
        "error", [
            400, 404, 409, 422, 500, 501
        ]
    )
    def test_expected_unhandled_requests(
        self, mock_api_request, error
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            )
        ]
        with pytest.raises(exceptions.APIError):
            session.full_cache()


class TestProtonSessionWrapperLoadsCache():

    @classmethod
    def setup_class(cls):
        with open(conn_state_filepath, "w") as a:
            json.dump({
                "connected_server": "conn_test",
                "connected_protocol": "tcp",
                "connected_time": 0000000
            }, a)

        with open(last_conn_state_filepath, "w") as f:
            json.dump({
                "connected_server": "last_conn_test",
                "last_connect_ip": "192.168.0.1"
            }, f)

        with open(server_cache_filepath, "w") as c:
            json.dump({
                "full_cache_timestamp": "1606390288",
                "loads_cache_timestamp": "1606390288"
            }, c)

    @classmethod
    def teardown_class(cls):
        os.remove(conn_state_filepath)
        os.remove(last_conn_state_filepath)
        os.remove(server_cache_filepath)
        os.remove(TEST_CACHED_SERVERLIST)

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.core.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    def test_loads_cache(self, mock_api_request):
        mock_api_request.side_effect = [
            RAW_LOADS_LIST
        ]
        session.full_cache()
        with open(TEST_CACHED_SERVERLIST) as f:
            file = json.load(f)

            assert file["LogicalServers"][0]["Load"] == "55"

    @pytest.mark.parametrize(
        "error", [
            400, 404, 409, 422, 500, 501
        ]
    )
    def test_expected_unhandled_requests(
        self, mock_api_request, error
    ):
        mock_api_request.side_effect = [
            ProtonError(
                {
                    "Code": error,
                    "Error": "Error code {}".format(error)
                }
            )
        ]
        with pytest.raises(exceptions.APIError):
            session.loads_cache()


class TestUnits():

    @pytest.mark.parametrize(
        "method", [
            ProtonSessionAPIMethodEnum.API_REQUEST,
            ProtonSessionAPIMethodEnum.AUTHENTICATE,
            ProtonSessionAPIMethodEnum.LOGOUT,
            ProtonSessionAPIMethodEnum.FULL_CACHE,
            ProtonSessionAPIMethodEnum.LOADS_CACHE,
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
