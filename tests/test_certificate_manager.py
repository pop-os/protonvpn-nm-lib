from lib import exceptions
import pytest

from lib.services.plugin_manager import PluginManager
from lib.services.certificate_manager import CertificateManager
import proton
import json
import os
import shutil


SERVERS = [
        {
            "Name": "test#5", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-05.protonvpn.com", "Tier": 1, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "m3-9M9TDapzElDMw5VO28-9DhaA0r1XXdPjg0MMNb5ki7cmEosVFf0metcsHchD8E98BQpiV_9QfmyXgqaQQ7Q==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.227", "ExitIP": "195.158.248.227", "Domain": "pt-05.protonvpn.com", "ID": "2-NIsqlNbgq1R3qf-HYdVCOm4essypLJf7Ui4XT-LMPGnipRRJ8oB7zn9PzwEsdBXii0CWdm2sO3CiSD2NI9Pw==", "Status": 1}], "Load": 11, "Score": 1.00316551
        },
        {
            "Name": "test#6", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-06.protonvpn.com", "Tier": 1, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "nsKp7TSiN2EGt6ZOw81kI9ohUqqb4hnDQV_XwD76z1l1O8D45pLNAMSBynQ_empiuKEQu0Zq6jBN5X1fMNaxxg==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.228", "ExitIP": "195.158.248.228", "Domain": "pt-06.protonvpn.com", "ID": "iB_Q4O344r_LOhZWjVZsU1lO7MNBjT3pR8vDFhPYqym8MCxNTlBJwJwIiMsxwwbSlT_McjX85JNxYtS3nMdJjw==", "Status": 1}], "Load": 6, "Score": 1.00283101
        },
        {
            "Name": "test#7", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-07.protonvpn.com", "Tier": 1, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "5gXO0B4g3q1gI_-f9x3xPVZYhtf2K0ipYVYe7H9NkeGjcAWxN1WZfHqUmS36MH8xVs66PEVY0LLVbEfrGDUi7A==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.229", "ExitIP": "195.158.248.229", "Domain": "pt-07.protonvpn.com", "ID": "5ftRWs9dLCDamZcUFEq_tOLK0-p9Z0U2I7RpVq7dkpPQ4X53TGnCTAsoZrMiLnNmX2mMqI8vjaAowoPH6adyTA==", "Status": 1}], "Load": 7, "Score": 1.00286911
        },
        {
            "Name": "test#8", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-08.protonvpn.com", "Tier": 2, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "6jz6aTZ_Fsi9vc6CuOrehmJwx4dYfXGB5S92dvD_6-woiYM5pazvXyvhnt_DSNpVE_Scb9atTI8sIr-_pDUO-w==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.230", "ExitIP": "195.158.248.230", "Domain": "pt-08.protonvpn.com", "ID": "vAD1v-T3yNqUq0-P6dfLXtnvtyg0nNvocWyjbQS5UiGf4ll_te7gAx9pisbXnlCRYURFZf46SFbg6Oh74trpMw==", "Status": 1}], "Load": 37, "Score": 0.01796211
        },
        {
            "Name": "test#9", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-09.protonvpn.com", "Tier": 2, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "C-P4TPPA0Nsvwl56YS9EPXFcXdt-cmIYqnuxOF8gCBJ4koTf90FJgU2fOh8o6qeN5ParA2SbVnU4UjwyeNlU3w==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.231", "ExitIP": "195.158.248.231", "Domain": "pt-09.protonvpn.com", "ID": "jWX4uC1V6Nib4EHf19aHN3bC7K5HRChaFBzBZSOrCkE7Dlx0LX0tQqw89Stl45PZXvpJ5hH_BUcpB_Ms3UUIeQ==", "Status": 1}], "Load": 41, "Score": 0.02344251
        },
        {
            "Name": "test#4", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-10.protonvpn.com", "Tier": 2, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "o7L9rJE0tap7eyFvwbY1hVLfNhUuEZ0f1K8sFCGwGaJESqW55c6H1KCZOz1XtHBEOQxX8ctJwheVj4mgq3tUQA==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.232", "ExitIP": "195.158.248.232", "Domain": "pt-10.protonvpn.com", "ID": "BRubRvHB7nHQ0D0fS1auCGRbF0rFou5mXGim8oDcc6hL5C1CQSRb1aJdda-Br_A129hxu9GXMNdKrw24PPZhig==", "Status": 1}], "Load": 23, "Score": 0.00641631
        },
        {
            "Name": "test#3", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-11.protonvpn.com", "Tier": 2, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "9pwZYvAUxbO59navIdbD1FO2xqTdnm7K1UzkIOjxWhZHH0L-T5glA06aV4iDe2qZhgecKvjfD1YPIaHtfGjLdA==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.233", "ExitIP": "195.158.248.233", "Domain": "pt-11.protonvpn.com", "ID": "a4ll9xxW2JS5RgqilYbYYWUGDKVHXRGJ8iOIklOgPHcuioB27sZq-g3A7VowQmoQmr7iuT9hRY21vN0zl8v4Jg==", "Status": 1}], "Load": 27, "Score": 0.00867111
        },
        {
            "Name": "test#2", "EntryCountry": "PT", "ExitCountry": "PT", "Domain": "pt-12.protonvpn.com", "Tier": 2, "Features": 0, "Region": "null", "City": "Lisbon", "ID": "spwi-5m18BvDaBH35ppz5vQT9cxLOz7BArsEEDMNSyX1AYFDQvQMUdr1WbM7qcisimnZrLpBfOTO706-tPu6MQ==", "Location": {"Lat": 38.72, "Long": -9.13}, "Status": 1, "Servers": [{"EntryIP": "195.158.248.234", "ExitIP": "195.158.248.234", "Domain": "pt-12.protonvpn.com", "ID": "PZ6BjoLV-GVySGnZNeGufSxDEw_W6Pb_CF79fxBWSKM-iUucnhQhAVZSSrGn8VRKgon3Ht_cTU2LDj7CDCk9sw==", "Status": 1}], "Load": 55, "Score": 0.05267871
        }
]

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

MOCK_DATA_JSON = json.dumps(MOCK_AUTHDATA)
session = proton.Session.load(json.loads(MOCK_DATA_JSON))
PWD = os.path.dirname(os.path.abspath(__file__))
TEST_CERTS = os.path.join(PWD, "test_certs")


class TestCertificateManager:
    cert_man = CertificateManager()

    @classmethod
    def setup_class(cls):
        try:
            os.mkdir(TEST_CERTS)
        except FileExistsError:
            shutil.rmtree(TEST_CERTS)
            os.mkdir(TEST_CERTS)

    @classmethod
    def teardown_class(cls):
        shutil.rmtree(TEST_CERTS)

    @pytest.mark.parametrize(
        "protocol,session,servername,servers,cert_path",
        [
            (
                "tcp", session,
                "test#2", SERVERS,
                os.path.join(TEST_CERTS, "test#2.ovpn")
            ),
            (
                "udp", session,
                "test#3", SERVERS,
                os.path.join(TEST_CERTS, "test#3.ovpn")
            ),
        ]
    )
    def test_correct_generate_vpn_cert(
        self, protocol, session,
        servername, servers, cert_path
    ):
        self.cert_man.generate_vpn_cert(
            protocol,
            session,
            servername,
            servers,
            cert_path
        )

    @pytest.mark.parametrize(
        "protocol,excp",
        [
            ("tdp", exceptions.IllegalVPNProtocol),
            ("ufc", exceptions.IllegalVPNProtocol),
            ("", exceptions.IllegalVPNProtocol),
            (2, TypeError),
            ({}, TypeError),
            ([], TypeError),
            (None, TypeError),
            (False, TypeError),
        ]
    )
    def test_incorrect_protocol_generate_vpn_cert(self, protocol, excp):
        with pytest.raises(excp):
            self.cert_man.generate_vpn_cert(
                protocol, session,
                "test#2", SERVERS,
                os.path.join(TEST_CERTS, "test#2.ovpn"),
            )

    @pytest.mark.parametrize(
        "session,excp",
        [
            ("session", TypeError),
            ("", TypeError),
            (2, TypeError),
            ({}, TypeError),
            ([], TypeError),
            (None, TypeError),
            (False, TypeError),
        ]
    )
    def test_incorrect_session_generate_vpn_cert(self, session, excp):
        with pytest.raises(excp):
            self.cert_man.generate_vpn_cert(
                "tcp", session,
                "test#2", SERVERS,
                os.path.join(TEST_CERTS, "test#2.ovpn"),
            )

    # @pytest.mark.parametrize(
    #     "servername,excp",
    #     [
    #         ("_", exceptions.IllegalServername),
    #         ("test_server@13", exceptions.IllegalServername),
    #         ("", exceptions.IllegalServername),
    #         ("#42", exceptions.IllegalServername),
    #         ("234#", exceptions.IllegalServername),
    #         ("hello#", exceptions.IllegalServername),
    #         (56, TypeError),
    #         ({}, TypeError),
    #         ([], TypeError),
    #         (None, TypeError),
    #         (False, TypeError),
    #     ]
    # )
    # def test_incorrect_servername_generate_vpn_cert(self, servername, excp):
    #     with pytest.raises(excp):
    #         self.cert_man.generate_vpn_cert(
    #             "tcp", session,
    #             servername, SERVERS,
    #             os.path.join(TEST_CERTS, "test#3.ovpn"),
    #         )

    @pytest.mark.parametrize(
        "servers,excp",
        [
            ("", TypeError),
            ("test", TypeError),
            (dict(test="test"), TypeError),
            (56, TypeError),
            ({}, TypeError),
            ([], ValueError),
            (None, TypeError),
            (False, TypeError),
        ]
    )
    def test_incorrect_servers_generate_vpn_cert(self, servers, excp):
        with pytest.raises(excp):
            self.cert_man.generate_vpn_cert(
                "tcp", session,
                "test#3", servers,
                os.path.join(TEST_CERTS, "test#3.ovpn"),
            )

    def test_correct_generate_openvpn_cert(self):
        self.cert_man.generate_openvpn_cert(
            "test#3", SERVERS, os.path.join(TEST_CERTS, "test#3.ovpn"), "tcp"
        )

    def test_correct_generate_strongswan_cert(self):
        self.cert_man.generate_strongswan_cert(
            "test#4", SERVERS, os.path.join(TEST_CERTS, "test#4.sswan")
        )

    def test_correct_generate_wireguard_cert(self):
        self.cert_man.generate_wireguard_cert(
            "test#5", SERVERS, os.path.join(TEST_CERTS, "test#5.wg")
        )
