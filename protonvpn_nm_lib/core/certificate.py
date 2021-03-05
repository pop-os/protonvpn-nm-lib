import os

import jinja2
from jinja2 import Environment, FileSystemLoader

from .. import exceptions
from ..constants import (
    CACHED_OPENVPN_CERTIFICATE, OPENVPN_TEMPLATE,
    PROTON_XDG_CACHE_HOME, TEMPLATES
)
from ..enums import ProtocolEnum, ProtocolPortEnum
from ..logger import logger
from . import capture_exception


class Certificate:
    """Certificate class.

    Generates VPN certificate.
    """
    def generate_vpn_cert(
        self, protocol,
        servername, ip_list, exit_IP, cached_cert=CACHED_OPENVPN_CERTIFICATE
    ):
        """Abstract method that generates a vpn certificate.

        Args:
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
            servername (string): servername [PT#1]
            ip_list (list): the ips for the selected server
            cached_cert (string): path to where a certificate is to be cached
                (optional)
        Returns:
            string: path to cached certificate
        """
        logger.info("Generating VPN certificate")
        protocol_dict = {
            ProtocolEnum.TCP: self.generate_openvpn_cert,
            ProtocolEnum.UDP: self.generate_openvpn_cert,
            ProtocolEnum.IKEV2: self.generate_strongswan_cert,
            ProtocolEnum.WIREGUARD: self.generate_wireguard_cert
        }

        if not isinstance(protocol, ProtocolEnum):
            err_msg = "Incorrect object type, "\
                "ProtocolEnum is expected but got {} instead".format(
                    type(protocol)
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        if not isinstance(servername, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(servername))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        if not isinstance(ip_list, list):
            err_msg = "Incorrect object type, "\
                "list is expected but got {} instead".format(type(ip_list))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        logger.info("Type checks passed")

        if len(ip_list) == 0:
            logger.error(
                "[!] ValueError: No servers were provided. Raising exception."
            )
            raise ValueError("No servers were provided")

        try:
            return protocol_dict[protocol](
                servername, ip_list,
                cached_cert, protocol
            )
        except KeyError as e:
            logger.exception("[!] IllegalVPNProtocol: {}".format(e))
            raise exceptions.IllegalVPNProtocol(e)
        except jinja2.exceptions.TemplateNotFound as e:
            logger.exception("[!] jinja2.TemplateNotFound: {}".format(e))
            raise jinja2.exceptions.TemplateNotFound(e)
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)

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
        logger.info("Generating OpenVPN certificate")
        ports = {
            ProtocolEnum.TCP.value: ProtocolPortEnum.TCP.value,
            ProtocolEnum.UDP.value: ProtocolPortEnum.UDP.value
        }

        j2_values = {
            "openvpn_protocol": protocol.value,
            "serverlist": ip_list,
            "openvpn_ports": [ports[protocol.value]],
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
        logger.info("Generating strongswan certificate")
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
        logger.info("Generating Wireguard certificate")
        return True

    @staticmethod
    def delete_cached_certificate(filename):
        """Delete cached certificate.

        Args:
            filename (string): path to cached certificate
        """
        logger.info("Deleting cached certificate")
        os.remove(filename)
