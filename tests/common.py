import os
import json

MOCK_AUTHDATA = {
    "api_url": "https://api.protonvpn.ch/tests/ping",
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

SERVERS = [
    {
        "Name": "test#5",
        "EntryCountry": "PT",
        "ExitCountry": "PT",
        "Domain": "pt-89.webtest.com",
        "Tier": 1,
        "Features": 0,
        "Region": "null",
        "City": "Lisbon",
        "ID": "SOME_ID",
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
                "Domain": "pt-89.webtest.com", "ID": "SOME_ID",
                "Status": 1
            }
        ],
        "Load": 11, "Score": 1.00316551
    },
    {
        "Name": "test#6",
        "EntryCountry": "PT",
        "ExitCountry": "PT",
        "Domain": "pt-99.webtest.com",
        "Tier": 1, "Features": 0,
        "Region": "null", "City": "Lisbon",
        "ID": "SOME_ID",
        "Location": {
            "Lat": 38.72, "Long": -9.13
        },
        "Status": 1,
        "Servers": [
            {
                "EntryIP": "255.255.255.0", "ExitIP": "255.255.255.0",
                "Domain": "pt-99.webtest.com",
                "ID": "SOME_ID",
                "Status": 1
            }
        ], "Load": 6, "Score": 1.00283101
    },
]

MOCK_DATA_JSON = json.dumps(MOCK_AUTHDATA)
PWD = os.path.dirname(os.path.abspath(__file__))
CERT_FOLDER = os.path.join(PWD, "certificates/connection_manager")
TEST_CERTS = os.path.join(PWD, "test_certs")
PLUGIN_CERT_FOLDER = os.path.join(PWD, "certificates/plugin_manager")
TEST_CACHED_SERVERFILE = os.path.join(PWD, "test_cached_serverfile")
