import json
import os
import shutil

import pytest

from common import (
    MOCK_DATA_JSON, SERVERS, TEST_CERTS,
    CertificateManager, ProtonSessionWrapper, UserManager, exceptions
)

um = UserManager(
    keyring_service="TestCertitifcateManager",
    keyring_sessiondata="TestCertManSessionData",
    keyring_userdata="TestCertManUserData",
    keyring_proton_user="TestCertManUser"
)
session = ProtonSessionWrapper.load(json.loads(MOCK_DATA_JSON), um)


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
        "protocol,,servername,servers,cert_path",
        [
            (
                "tcp",
                "test#5", SERVERS,
                os.path.join(TEST_CERTS, "test#5.ovpn")
            ),
            (
                "udp",
                "test#6", SERVERS,
                os.path.join(TEST_CERTS, "test#6.ovpn")
            ),
        ]
    )
    def test_correct_generate_vpn_cert(
        self, protocol,
        servername, servers, cert_path
    ):
        self.cert_man.generate_vpn_cert(
            protocol,
            servername,
            servers,
            cert_path
        )

    @pytest.mark.parametrize(
        "protocol,servername,excp",
        [
            ("tdp", "test#5", exceptions.IllegalVPNProtocol),
            ("udp", 5, TypeError),
            ("ufc", "test#5", exceptions.IllegalVPNProtocol),
            ("", "test#5", exceptions.IllegalVPNProtocol),
            (2, "test#5", TypeError),
            ({}, "test#5", TypeError),
            ([], "test#5", TypeError),
            (None, "test#5", TypeError),
            (False, "test#5", TypeError),
        ]
    )
    def test_incorrect_protocol_generate_vpn_cert(
        self, protocol, servername, excp
    ):
        with pytest.raises(excp):
            self.cert_man.generate_vpn_cert(
                protocol,
                servername, SERVERS,
                os.path.join(TEST_CERTS, "test#5.ovpn"),
            )

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
                "tcp",
                "test#5", servers,
                os.path.join(TEST_CERTS, "test#5.ovpn"),
            )

    def test_correct_generate_openvpn_cert(self):
        self.cert_man.generate_openvpn_cert(
            "test#6", SERVERS, os.path.join(TEST_CERTS, "test#6.ovpn"), "tcp"
        )

    def test_correct_generate_strongswan_cert(self):
        self.cert_man.generate_strongswan_cert(
            "test#5", SERVERS, os.path.join(TEST_CERTS, "test#5.sswan")
        )

    def test_correct_generate_wireguard_cert(self):
        self.cert_man.generate_wireguard_cert(
            "test#6", SERVERS, os.path.join(TEST_CERTS, "test#6.wg")
        )
