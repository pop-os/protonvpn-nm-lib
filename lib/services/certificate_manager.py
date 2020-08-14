from lib import exceptions
from jinja2 import Environment, FileSystemLoader
import os
from lib.constants import (
    CACHED_OPENVPN_CERTIFICATE, OPENVPN_TEMPLATE,
    TEMPLATES, PROTON_XDG_CACHE_HOME
)
from proton.api import Session


class CertificateManager:
    def generate_vpn_cert(
        self, protocol, session,
        servername, ip_list, cached_cert=CACHED_OPENVPN_CERTIFICATE
    ):
        protocol_dict = {
            "tcp": self.generate_openvpn_cert,
            "udp": self.generate_openvpn_cert,
            "ikve2": self.generate_strongswan_cert,
            "wireguard": self.generate_wireguard_cert
        }

        if not isinstance(protocol, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(protocol))
            )

        if not isinstance(session, Session):
            raise TypeError(
                "Incorrect object type, "
                + "{} is expected ".format(type(Session))
                + "but got {} instead".format(type(protocol))
            )

        if not isinstance(servername, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(servername))
            )

        if not isinstance(ip_list, list):
            raise TypeError(
                "Incorrect object type, "
                + "list is expected but got {} instead".format(type(ip_list))
            )

        if len(ip_list) == 0:
            raise ValueError("No servers were provided")

        print(servername)

        protocol = protocol.lower()

        try:
            return protocol_dict[protocol](
                servername, ip_list,
                cached_cert, protocol
            )
        except KeyError as e:
            raise exceptions.IllegalVPNProtocol(e)

    def generate_openvpn_cert(
        self, servername, ip_list,
        cached_cert, protocol
    ):
        port = {"udp": 1194, "tcp": 443}

        # Ports gets casted to a list
        # instead of just a single port to make it iterable
        j2_values = {
            "openvpn_protocol": protocol,
            "serverlist": ip_list,
            "openvpn_ports": [port[protocol.lower()]],
        }

        j2 = Environment(loader=FileSystemLoader(TEMPLATES))

        template = j2.get_template(OPENVPN_TEMPLATE)

        if not os.path.isdir(PROTON_XDG_CACHE_HOME):
            os.mkdir(PROTON_XDG_CACHE_HOME)

        with open(cached_cert, "w") as f:
            f.write(template.render(j2_values))

        return cached_cert

    def generate_strongswan_cert(
        self, servername, ip_list,
        cached_cert, _=None
    ):
        print("Generate strongswan")
        return True

    def generate_wireguard_cert(
        self, servername, ip_list,
        cached_cert, _=None
    ):
        print("Generate wireguard")
        return True

    @staticmethod
    def delete_cached_certificate(filename):
        os.remove(filename)
