import os

from jinja2 import Environment, FileSystemLoader
from proton.api import Session

from lib import exceptions
from lib.constants import (CACHED_OPENVPN_CERTIFICATE, OPENVPN_TEMPLATE,
                           PROTON_XDG_CACHE_HOME, TEMPLATES)
from lib.enums import ProtocolEnum, ProtocolPortEnum


class CertificateManager:
    def generate_vpn_cert(
        self, protocol, session,
        servername, ip_list, cached_cert=CACHED_OPENVPN_CERTIFICATE
    ):
        """Abstract method that generates a vpn certificate.

        Args:
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
            session (proton.api.Session): the current user session
            servername (string): servername [PT#1]
            ip_list (list): the ips for the selected server
            cached_cert (string): path to where a certificate is to be cached
                (optional)
        Returns:
            string: path to cached certificate
        """
        protocol_dict = {
            ProtocolEnum.TCP: self.generate_openvpn_cert,
            ProtocolEnum.UDP: self.generate_openvpn_cert,
            ProtocolEnum.IKEV2: self.generate_strongswan_cert,
            ProtocolEnum.WIREGUARD: self.generate_wireguard_cert
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
        """Generates openvpn certificate.

        Args:
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
            servername (string): servername [PT#1]
            ip_list (list): the ips for the selected server
            cached_cert (string): path to where a certificate is to be cached
        Returns:
            string: path to where a certificate is cached
        """
        ports = {
            ProtocolEnum.TCP: ProtocolPortEnum.TCP,
            ProtocolEnum.UDP: ProtocolPortEnum.UDP
        }

        j2_values = {
            "openvpn_protocol": protocol,
            "serverlist": ip_list,
            "openvpn_ports": [ports[protocol]],
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
        """Generates ikev2/strongswan certificate.

        Args:
            servername (string): servername [PT#1]
            ip_list (list): the ips for the selected server
            cached_cert (string): path to where a certificate is to be cached
        Returns:
            bool
        """
        print("Generate strongswan")
        return True

    def generate_wireguard_cert(
        self, servername, ip_list,
        cached_cert, _=None
    ):
        """Generates wireguard certificate.

        Args:
            servername (string): servername [PT#1]
            ip_list (list): the ips for the selected server
            cached_cert (string): path to where a certificate is to be cached
        Returns:
            bool
        """
        print("Generate wireguard")
        return True

    @staticmethod
    def delete_cached_certificate(filename):
        """Delete cached certificate.

        Args:
            filename (string): path to cached certificate
        """
        os.remove(filename)
