import json
import os
import shutil
from unittest.mock import patch

import pytest

from common import (PWD, CACHED_OPENVPN_CERTIFICATE, MOCK_DATA_JSON,
                    MOCK_SESSIONDATA, RAW_SERVER_LIST, SERVERS,
                    TEST_CACHED_SERVERFILE, CertificateManager,
                    ProtonSessionWrapper, ServerManager, UserManager,
                    UserConfigurationManager, MetadataEnum, ProtocolEnum)

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


class TestUnitServerManager:
    server_man = ServerManager(
        CertificateManager(),
        um
    )
    MOCKED_SESSION = ProtonSessionWrapper(
        api_url="https://localhost",
        user_manager=um
    )

    @classmethod
    def setup_class(cls):
        try:
            os.mkdir(TEST_CACHED_SERVERFILE)
        except FileExistsError:
            shutil.rmtree(TEST_CACHED_SERVERFILE)
            os.mkdir(TEST_CACHED_SERVERFILE)

        um.store_data(
            data=MOCK_SESSIONDATA,
            keyring_username=TEST_KEYRING_SESSIONDATA,
            keyring_service=TEST_KEYRING_SERVICE
        )
        um.store_data(
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
        um.store_data(
            data={"test_proton_username": "test_server_man_user"},
            keyring_username=TEST_KEYRING_PROTON_USER,
            keyring_service=TEST_KEYRING_SERVICE,
            store_user_data=False
        )

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(TEST_CACHED_SERVERFILE)
        um.delete_stored_data(TEST_KEYRING_PROTON_USER, TEST_KEYRING_SERVICE)
        um.delete_stored_data(TEST_KEYRING_SESSIONDATA, TEST_KEYRING_SERVICE)
        um.delete_stored_data(TEST_KEYRING_USERDATA, TEST_KEYRING_SERVICE)

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    @pytest.mark.parametrize("servername", ["#", "", 5, None, {}, []])
    def test_get_incorrect_get_pyshical_ip_list(
        self, servername, mock_api_request
    ):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        (
            _servername,
            server_domain,
            server_feature,
            filtered_servers,
            servers
        ) = self.server_man.get_config_for_fastest_server(
            session=self.MOCKED_SESSION,
        )
        with pytest.raises(IndexError):
            self.server_man.get_physical_server_list(
                servername, SERVERS, filtered_servers
            )

    def test_get_correct_get_pyshical_ip_list(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        (
            servername,
            server_domain,
            server_feature,
            filtered_servers,
            servers
        ) = self.server_man.get_config_for_fastest_server(
            session=self.MOCKED_SESSION,
        )
        servers = self.server_man.get_physical_server_list(
            "TEST#5", SERVERS, filtered_servers
        )
        assert servers[0]["Domain"] == "pt-89.webtest.com"

    def test_get_existing_label(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        (
            servername,
            server_domain,
            server_feature,
            filtered_servers,
            servers
        ) = self.server_man.get_config_for_specific_server(
            session=self.MOCKED_SESSION, servername="TEST#5"
        )
        servers = self.server_man.get_physical_server_list(
            servername, servers, filtered_servers
        )

        server = self.server_man.get_random_physical_server(servers)
        label = self.server_man.get_server_label(server)
        assert label == "TestLabel"

    def test_get_nonexisting_label(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        (
            servername,
            server_domain,
            server_feature,
            filtered_servers,
            servers
        ) = self.server_man.get_config_for_specific_server(
            session=self.MOCKED_SESSION, servername="TEST#6"
        )
        servers = self.server_man.get_physical_server_list(
            servername, servers, filtered_servers
        )

        server = self.server_man.get_random_physical_server(servers)
        label = self.server_man.get_server_label(server)
        assert label is None

    def test_get_server_IP(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        (
            servername,
            server_domain,
            server_feature,
            filtered_servers,
            servers
        ) = self.server_man.get_config_for_specific_server(
            session=self.MOCKED_SESSION, servername="TEST#6"
        )
        servers = self.server_man.get_physical_server_list(
            servername, servers, filtered_servers
        )

        server = self.server_man.get_random_physical_server(servers)
        ips = self.server_man.get_server_entry_exit_ip(server)
        assert ips == ("255.211.255.0", "255.211.255.0")

    @pytest.fixture
    def empty_server_pool(self):
        server_pool = []
        return server_pool

    @pytest.fixture
    def full_server_pool(self):
        feature = 0
        server_pool = [s for s in SERVERS if s["Features"] == feature]
        return server_pool

    def test_get_fastest_server_empty_pool(self, empty_server_pool):
        with pytest.raises(IndexError):
            self.server_man.get_fastest_server(empty_server_pool)

    def test_get_fastest_server_full_pool(self, full_server_pool):
        self.server_man.get_fastest_server(full_server_pool)

    @pytest.mark.parametrize(
        "servername",
        [
            "TEST#6", "TEST#5",
        ]
    )
    def test_correct_extract_server_value(self, servername):
        self.server_man.extract_server_value(servername, "Servers", SERVERS)

    @pytest.mark.parametrize(
        "servername",
        [
            "", "test#50",
            "#6", "test",
            123, None,
            False
        ]
    )
    def test_incorrect_extract_server_value(self, servername):
        with pytest.raises(IndexError):
            self.server_man.extract_server_value(
                servername, "Servers", SERVERS
            )

    @pytest.mark.parametrize(
        "cc,country",
        [
            ("BR", "Brazil"),
            ("BS", "Bahamas"),
            ("GR", "Greece"),
            ("GQ", "Equatorial Guinea"),
            ("GP", "Guadeloupe"),
            ("JP", "Japan"),
            ("GY", "Guyana"),
        ]
    )
    def test_correct_country_name(self, cc, country):
        assert self.server_man.extract_country_name(cc) == country

    @pytest.mark.parametrize(
        "cc,country",
        [
            ("BS", "Brazil"),
            ("BR", "Bahamas"),
            ("GQ", "Greece"),
            ("GR", "Equatorial Guinea"),
            ("JP", "Guadeloupe"),
            ("GP", "Japan"),
            ("Z", "Guyana"),
            ("", "Guyana"),
            (5, "Guyana"),
        ]
    )
    def test_incorrect_extract_country_name(self, cc, country):
        assert self.server_man.extract_country_name(cc) != country

    @pytest.mark.parametrize(
        "servername",
        [
            "PT#5",
            "SE-PT#123",
            "CH#18-TOR",
            "US-CA#999",
            "CH-FI#8",
            "ch-fi#8",
        ]
    )
    def test_valid_servername(self, servername):
        resp = self.server_man.is_servername_valid(servername)
        assert resp is True

    @pytest.mark.parametrize(
        "servername",
        [
            "_#1",
            "123#412",
            "#123",
            "test2#412",
            "CH#",
            "#",
            "5",
        ]
    )
    def test_invalid_servername(self, servername):
        resp = self.server_man.is_servername_valid(servername)
        assert resp is False

    @pytest.mark.parametrize(
        "servername",
        [
            [], {}, 132
        ]
    )
    def test_more_incorrect_servernames(self, servername):
        with pytest.raises(TypeError):
            self.server_man.is_servername_valid(servername)


class TestIntegrationServerManager:
    server_man = ServerManager(
        CertificateManager(),
        um
    )
    server_man.CACHED_SERVERLIST = TEST_CACHED_SERVERLIST
    MOCKED_SESSION = ProtonSessionWrapper(
        api_url="https://localhost",
        user_manager=um
    )

    @classmethod
    def setup_class(cls):
        um.store_data(
            data=MOCK_SESSIONDATA,
            keyring_username=TEST_KEYRING_SESSIONDATA,
            keyring_service=TEST_KEYRING_SERVICE
        )
        um.store_data(
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
        um.store_data(
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
        um.delete_stored_data(TEST_KEYRING_PROTON_USER, TEST_KEYRING_SERVICE)
        um.delete_stored_data(TEST_KEYRING_SESSIONDATA, TEST_KEYRING_SERVICE)
        um.delete_stored_data(TEST_KEYRING_USERDATA, TEST_KEYRING_SERVICE)
        os.remove(TEST_CACHED_SERVERLIST)

    @pytest.fixture
    def mock_api_request(self):
        mock_get_patcher = patch(
            "protonvpn_nm_lib.services.proton_session_wrapper."
            "Session.api_request"
        )
        yield mock_get_patcher.start()
        mock_get_patcher.stop()

    def test_correct_generate_connect_fastest(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        servername, *rest = self.server_man.get_config_for_fastest_server(
            self.MOCKED_SESSION,
        )
        assert servername == "TEST_IPV6#11"

    def test_correct_generate_connect_country(self):
        (
            servername,
            *rest
        ) = self.server_man.get_config_for_fastest_server_in_country(
            session=self.MOCKED_SESSION,
            country_code="PT",
        )
        assert servername == "TEST#6"

    def test_correct_generate_connect_direct(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        server = "TEST#6"
        (
            servername,
            *rest
        ) = self.server_man.get_config_for_specific_server(
            session=self.MOCKED_SESSION,
            servername=server,
        )
        assert servername == server

    @pytest.mark.parametrize(
        "feature,servername", [
            ("sc", "TEST_SECURE_CORE#7"),
            ("tor", "TEST_TOR#8"),
            ("p2p", "TEST_P2P#9"),
            ("stream", "TEST_STREAMING#10"),
            ("ipv6", "TEST_IPV6#11")
        ]
    )
    def test_correct_generate_connect_feature(self, feature, servername):
        (
            _servername,
            *rest
        ) = self.server_man.get_config_for_fastest_server_with_specific_feature( # noqa
            session=self.MOCKED_SESSION,
            feature=feature,
        )
        assert servername == _servername

    def test_correct_generate_connect_random(self):
        servername, *rest = self.server_man.get_config_for_random_server(
            session=self.MOCKED_SESSION,
        )
        assert servername in [server["Name"] for server in SERVERS]

    def test_correct_generate_server_certificate(self):
        (
            servername,
            server_domain,
            server_feature,
            filtered_servers,
            servers
        ) = self.server_man.get_config_for_fastest_server(
            session=self.MOCKED_SESSION,
        )
        (
            cert_fp,
            matching_domain,
            entry_IP,
            server_label
        ) = self.server_man.generate_server_certificate(
            servername, server_domain, server_feature,
            ProtocolEnum.TCP, servers, filtered_servers
        )

        assert True == (True if os.path.isfile(cert_fp) else False)
