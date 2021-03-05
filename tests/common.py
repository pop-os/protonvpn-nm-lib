import json
import os
from enum import Enum

from protonvpn_nm_lib import exceptions
from protonvpn_nm_lib.constants import (CACHED_OPENVPN_CERTIFICATE,
                                        ENV_CI_NAME, NETSHIELD_STATUS_DICT)
from protonvpn_nm_lib.core.certificate_manager import CertificateManager
from protonvpn_nm_lib.core.connection_manager import ConnectionManager
from protonvpn_nm_lib.core.connection_state_manager import \
    ConnectionStateManager
from protonvpn_nm_lib.core.ipv6_leak_protection import \
    IPv6LeakProtection
from protonvpn_nm_lib.core.killswitch import KillSwitch
from protonvpn_nm_lib.core.metadata_manager import MetadataManager
from protonvpn_nm_lib.core.plugin_manager import PluginManager
from protonvpn_nm_lib.core.proton_session_wrapper import ProtonSessionWrapper
from protonvpn_nm_lib.core.reconnector_manager import ReconnectorManager
from protonvpn_nm_lib.core.server_manager import ServerManager
from protonvpn_nm_lib.core.user_configuration_manager import \
    UserConfigurationManager
from protonvpn_nm_lib.core.user_manager import UserManager
from protonvpn_nm_lib.core.user_session_manager import UserSessionManager
from protonvpn_nm_lib.enums import (ClientSuffixEnum, ConnectionMetadataEnum,
                                    ConnectionTypeEnum, KillswitchStatusEnum,
                                    LastConnectionMetadataEnum,
                                    MetadataActionEnum, MetadataEnum,
                                    NetshieldStatusEnum,
                                    NetshieldTranslationEnum,
                                    NetworkManagerConnectionTypeEnum,
                                    ProtocolEnum, ProtocolImplementationEnum,
                                    ProtonSessionAPIMethodEnum,
                                    UserSettingConnectionEnum,
                                    UserSettingStatusEnum)


class TestServernameEnum(Enum):
    TEST_5 = "TE-TEST#5"
    TEST_6 = "TE-TEST#6"
    TEST_SC_7 = "TE-SECURECORE#7"
    TEST_TOR_8 = "TE-TOR#8"
    TEST_P2P_9 = "TE-P2P#9"
    TEST_STREAM_10 = "TE-STREAMING#10"
    TEST_IPV6_11 = "TE-IPV6#11"
    TEST_DISABLED_12 = "TE-DISABLED#12"


MOCK_SESSIONDATA = {
    "api_url": "https://localhost",
    "appversion": "4",
    "User-Agent": "CI Test User Agent",
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


MOCK_USER_DATA = {
    'Code': 1000,
    'VPN': {
        'ExpirationTime': 0,
        'Name': 'openvpn_user',
        'Password': 'openvpn_pwd',
        'GroupID': 'openvpn_user',
        'Status': 1,
        'PlanName': 'free',
        'MaxTier': 0,
        'MaxConnect': 2
    },
    'core': 5,
    'Subscribed': 0,
    'Delinquent': 0,
    'HasPaymentMethod': 1,
    'Credit': 0,
    'Currency': 'EUR'
}

SERVERS = [
    {
        "Name": TestServernameEnum.TEST_5.value,
        "EntryCountry": "PT",
        "ExitCountry": "PT",
        "Domain": "pt-89.webtest.com",
        "Tier": 1,
        "Features": 0,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID5",
        "Location": {
            "Lat": 38.72,
            "Long": -9.13
        },
        "Status": 1,
        "Servers":
        [
            {
                "EntryIP": "255.255.255.0",
                "ExitIP": "255.255.255.0",
                "Domain": "pt-89.webtest.com", "ID": "ID5",
                "Status": 1,
                "Label": "TestLabel"
            }
        ],
        "Load": 11, "Score": 1.00316551
    },
    {
        "Name": TestServernameEnum.TEST_6.value,
        "EntryCountry": "PT",
        "ExitCountry": "PT",
        "Domain": "pt-99.webtest.com",
        "Tier": 1,
        "Features": 0,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID6",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.211.255.0", "ExitIP": "255.211.255.0",
                "Domain": "pt-99.webtest.com",
                "ID": "ID6",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00283101
    },
    {
        "Name": TestServernameEnum.TEST_SC_7.value,
        "EntryCountry": "PT",
        "ExitCountry": "PT",
        "Domain": "pt-99.webtest.com",
        "Tier": 2,
        "Features": 1,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID7",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "pt-99.webtest.com",
                "ID": "ID7",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00183101
    },
    {
        "Name": TestServernameEnum.TEST_TOR_8.value,
        "EntryCountry": "CH",
        "ExitCountry": "CH",
        "Domain": "ch-99.webtest.com",
        "Tier": 2,
        "Features": 2,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID8",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "ch-99.webtest.com",
                "ID": "ID8",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00083101
    },
    {
        "Name": TestServernameEnum.TEST_P2P_9.value,
        "EntryCountry": "CH",
        "ExitCountry": "CH",
        "Domain": "ch-99.webtest.com",
        "Tier": 2,
        "Features": 4,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID8",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "ch-99.webtest.com",
                "ID": "ID8",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00073101
    },
    {
        "Name": TestServernameEnum.TEST_STREAM_10.value,
        "EntryCountry": "CH",
        "ExitCountry": "CH",
        "Domain": "ch-99.webtest.com",
        "Tier": 2,
        "Features": 8,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID8",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "ch-99.webtest.com",
                "ID": "ID8",
                "Status": 1,
            }
        ], "Load": 6, "Score": 1.00063101
    },
    {
        "Name": TestServernameEnum.TEST_IPV6_11.value,
        "EntryCountry": "CH",
        "ExitCountry": "CH",
        "Domain": "ch-99.webtest.com",
        "Tier": 2,
        "Features": 16,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID8",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "ch-99.webtest.com",
                "ID": "ID8",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00053101
    },
    {
        "Name": TestServernameEnum.TEST_DISABLED_12.value,
        "EntryCountry": "CH",
        "ExitCountry": "CH",
        "Domain": "ch-99.webtest.com",
        "Tier": 0,
        "Features": 0,
        "Region": "null",
        "City": "Lisbon",
        "ID": "ID8",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 0,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "ch-99.webtest.com",
                "ID": "ID8",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00043101
    },
]

LOADS = [
    {
        "ID": "ID5",
        "Load": "55",
        "Score": "0.55"
    },
    {
        "ID": "ID6",
        "Load": "66",
        "Score": "0.66"
    },
    {
        "ID": "ID7",
        "Load": "77",
        "Score": "0.77"
    },
]

RAW_SERVER_LIST = {
    "Code": 1000, "LogicalServers": SERVERS
}

RAW_LOADS_LIST = {
    "Code": 1000, "LogicalServers": LOADS
}

MOCK_DATA_JSON = json.dumps(MOCK_SESSIONDATA)
PWD = os.path.dirname(os.path.abspath(__file__))
CERT_FOLDER = os.path.join(PWD, "certificates/connection_manager")
PLUGIN_CERT_FOLDER = os.path.join(PWD, "certificates/plugin_manager")
TEST_CERTS = os.path.join(PWD, "test_certs")
TEST_CACHED_SERVERFILE = os.path.join(PWD, "test_cached_serverfile")
