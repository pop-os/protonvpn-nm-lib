import json
import os
import shutil
from unittest.mock import patch

import pytest

from common import (CACHED_OPENVPN_CERTIFICATE, MOCK_DATA_JSON,
                    MOCK_SESSIONDATA, PWD, RAW_SERVER_LIST, SERVERS,
                    TEST_CACHED_SERVERFILE, Certificate,
                    ConnectionTypeEnum, MetadataEnum, ProtocolEnum,
                    ProtonSessionWrapper, ServerManager, TestServernameEnum,
                    UserConfigurationManager, UserManager)

TEST_KEYRING_SERVICE = "TestServerManager"
TEST_KEYRING_SESSIONDATA = "TestServerManSessionData"
TEST_KEYRING_USERDATA = "TestServerManUserData"
TEST_KEYRING_PROTON_USER = "TestServerManUser"
TEST_CACHED_SERVERLIST = os.path.join(
    PWD, "test_server_manager_server_cache2.json"
)
conn_state_filepath = os.path.join(
    PWD, "test_server_manager.json"
)
last_conn_state_filepath = os.path.join(
    PWD, "test_server_manager.json"
)
remove_test_filepath = os.path.join(
    PWD, "remove_server_manager.json"
)

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
session = ProtonSessionWrapper.load(json.loads(MOCK_DATA_JSON), um)

session.CACHED_SERVERLIST = TEST_CACHED_SERVERLIST
session.METADATA_DICT = {
    MetadataEnum.CONNECTION: conn_state_filepath,
    MetadataEnum.LAST_CONNECTION: last_conn_state_filepath,
    MetadataEnum.SERVER_CACHE: remove_test_filepath
}
session.FULL_CACHE_TIME_EXPIRE = 1 / 120
session.LOADS_CACHE_TIME_EXPIRE = 1 / 120


class TestIntegrationServerManager:
    server_man = ServerManager(um)
    server_man.server_list_object.CACHED_SERVERLIST = TEST_CACHED_SERVERLIST
    MOCKED_SESSION = ProtonSessionWrapper(
        api_url="https://localhost",
        user_manager=um
    )

    @classmethod
    def setup_class(cls):
        um.session_data.store_data(
            data=MOCK_SESSIONDATA,
            keyring_username=TEST_KEYRING_SESSIONDATA,
            keyring_service=TEST_KEYRING_SERVICE
        )
        um.session_data.store_data(
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
        um.session_data.store_data(
            data={"test_proton_username": "test_server_man_user"},
            keyring_username=TEST_KEYRING_PROTON_USER,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=False
        )
        with open(TEST_CACHED_SERVERLIST, "w") as c:
            json.dump(RAW_SERVER_LIST, c, indent=4)

    @classmethod
    def teardown_class(cls):
        try:
            os.remove(CACHED_OPENVPN_CERTIFICATE)
        except FileNotFoundError:
            pass
        um.session_data.delete_stored_data(TEST_KEYRING_PROTON_USER, TEST_KEYRING_SERVICE)
        um.session_data.delete_stored_data(TEST_KEYRING_SESSIONDATA, TEST_KEYRING_SERVICE)
        um.session_data.delete_stored_data(TEST_KEYRING_USERDATA, TEST_KEYRING_SERVICE)
        os.remove(TEST_CACHED_SERVERLIST)

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.core.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    def test_correct_generate_connect_fastest(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        (
            server_list_object, server
        ) = self.server_man.get_config_for_fastest_server()
        assert server.name == TestServernameEnum.TEST_IPV6_11.value

    def test_correct_generate_connect_country(self):
        (
            server_list_object, server
        ) = self.server_man.get_config_for_fastest_server_in_country(
            country_code="PT",
        )
        assert server.name == TestServernameEnum.TEST_6.value

    def test_correct_generate_connect_direct(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        servername = TestServernameEnum.TEST_6.value
        (
            server_list_object, server
        ) = self.server_man.get_config_for_specific_server(
            servername=servername,
        )
        assert server.name == servername

    @pytest.mark.parametrize(
        "feature,servername", [
            (
                ConnectionTypeEnum.SECURE_CORE,
                TestServernameEnum.TEST_SC_7.value
            ),
            (ConnectionTypeEnum.TOR, TestServernameEnum.TEST_TOR_8.value),
            (ConnectionTypeEnum.PEER2PEER, TestServernameEnum.TEST_P2P_9.value),
            ("to-add-streaming", TestServernameEnum.TEST_STREAM_10.value),
            ("to-add-ipv6", TestServernameEnum.TEST_IPV6_11.value)
        ]
    )
    def test_correct_generate_connect_feature(self, feature, servername):
        (
            server_list_object, server
        ) = self.server_man.get_config_for_fastest_server_with_specific_feature( # noqa
            feature=feature,
        )
        assert server.name == servername

    def test_correct_generate_connect_random(self):
        server_list_object, server = self.server_man.get_config_for_random_server() # noqa
        assert server.name in [server["Name"] for server in SERVERS]
