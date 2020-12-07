import json
import os
import shutil
from unittest.mock import patch

import pytest

from common import (PWD, CACHED_OPENVPN_CERTIFICATE, MOCK_DATA_JSON,
                    MOCK_SESSIONDATA, RAW_SERVER_LIST, SERVERS,
                    TEST_CACHED_SERVERFILE, CertificateManager,
                    ProtonSessionWrapper, ServerManager, UserManager,
                    MetadataEnum, ProtocolEnum)

TEST_KEYRING_SERVICE = "TestServerManager"
TEST_KEYRING_SESSIONDATA = "TestServerManSessionData"
TEST_KEYRING_USERDATA = "TestServerManUserData"
TEST_KEYRING_PROTON_USER = "TestServerManUser"
TEST_CACHED_SERVERLIST = os.path.join(
    PWD, "test_server_manager_server_cache.json"
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

um = UserManager(
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
    def test_get_incorrect_generate_ip_list(self, servername):
        with pytest.raises(IndexError):
            self.server_man.generate_ip_list(servername, SERVERS)

    def test_get_correct_generate_ip_list(self):
        self.server_man.generate_ip_list("TEST#5", SERVERS)

    @pytest.fixture
    def empty_server_pool(self):
        feature = 2
        server_pool = [s for s in SERVERS if s["Features"] == feature]
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
            "US-CA#999"
        ]
    )
    def test_correct_servernames(self, servername):
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
    def test_incorrect_servernames(self, servername):
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
            json.dump(RAW_SERVER_LIST, c)

    @classmethod
    def teardown_class(cls):
        os.remove(CACHED_OPENVPN_CERTIFICATE)
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
        servername, domain, ip = self.server_man.generate(
            _method=self.server_man.fastest,
            command=["fastest", True],
            session=self.MOCKED_SESSION,
            protocol=ProtocolEnum.TCP
        )
        resp = False
        if servername and domain and ip:
            resp = True
        assert os.path.isfile(resp) is True

    @pytest.mark.parametrize(
        "session,proto,",
        [
            ("", 5),
            (5, ""),
            (object, object),
            ([], []),
            ({}, {}),
            (None, None),
            (MOCKED_SESSION, {}),
            (MOCKED_SESSION, None)
        ]
    )
    def test_incorrect_generate_session_proto(
        self, session, proto
    ):
        with pytest.raises(TypeError):
            self.server_man.generate(
                _method=self.server_man.fastest,
                command=["fastest", True],
                session=session,
                protocol=proto
            )

    @pytest.mark.parametrize(
        "method,command,error",
        [
            (None, None, TypeError),
            ("string", "test", TypeError),
            (object, object, TypeError),
            ([], [], IndexError),
            ({}, {}, TypeError),
            (None, None, TypeError),
            (MOCKED_SESSION, {}, TypeError),
            (MOCKED_SESSION, None, TypeError)
        ]
    )
    def test_incorrect_generate_method_command(
        self, method, command, error
    ):
        with pytest.raises(error):
            self.server_man.generate(
                _method=method,
                command=command,
                session=self.MOCKED_SESSION,
                protocol=ProtocolEnum.TCP
            )

    def test_correct_generate_connect_country(self):
        servername, domain, ip = self.server_man.generate(
            _method=self.server_man.country_f,
            command=["cc", "PT"],
            session=self.MOCKED_SESSION,
            protocol=ProtocolEnum.TCP
        )
        resp = False
        if servername and domain and ip:
            resp = True
        assert os.path.isfile(resp) is True

    def test_correct_generate_connect_direct(self, mock_api_request):
        mock_api_request.side_effect = [RAW_SERVER_LIST]
        servername, domain, ip = self.server_man.generate(
            _method=self.server_man.direct,
            command=["servername", "TEST#6"],
            session=self.MOCKED_SESSION,
            protocol=ProtocolEnum.TCP
        )

    def test_correct_generate_connect_feature(self):
        servername, domain, ip = self.server_man.generate(
            _method=self.server_man.feature_f,
            command=["sc", True],
            session=self.MOCKED_SESSION,
            protocol=ProtocolEnum.TCP
        )
        resp = False
        if servername and domain and ip:
            resp = True
        assert os.path.isfile(resp) is True

    def test_correct_generate_connect_random(self):
        servername, domain, ip = self.server_man.generate(
            _method=self.server_man.random_c,
            command=["random", True],
            session=self.MOCKED_SESSION,
            protocol=ProtocolEnum.TCP
        )
        resp = False
        if servername and domain and ip:
            resp = True
        assert os.path.isfile(resp) is True
