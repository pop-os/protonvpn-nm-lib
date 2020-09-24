import json
import os
import shutil

import proton
import pytest
from lib import exceptions
from lib.services.certificate_manager import CertificateManager

from common import MOCK_DATA_JSON, SERVERS, TEST_CERTS

session = proton.Session.load(json.loads(MOCK_DATA_JSON))


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
                "test#5", SERVERS,
                os.path.join(TEST_CERTS, "test#5.ovpn")
            ),
            (
                "udp", session,
                "test#6", SERVERS,
                os.path.join(TEST_CERTS, "test#6.ovpn")
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
                "test#5", SERVERS,
                os.path.join(TEST_CERTS, "test#5.ovpn"),
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
                "test#6", SERVERS,
                os.path.join(TEST_CERTS, "test#6.ovpn"),
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
    #             os.path.join(TEST_CERTS, "test#5.ovpn"),
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
