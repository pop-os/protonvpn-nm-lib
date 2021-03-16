from ..logger import logger
from .. import exceptions
import requests
from ..enums import KillswitchStatusEnum, ProtocolEnum, ConnectionTypeEnum
from ..constants import FLAT_SUPPORTED_PROTOCOLS
import re


class Utilities:

    @staticmethod
    def ensure_connectivity(killswith_setting):
        utils = Utilities()

        try:
            utils.ensure_internet_connection_is_available(
                killswith_setting
            )
            #LF: It's bad to loose the type of exception
        except exceptions.InternetConnectionError as e:
            raise Exception("\n{}".format(e))
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception(e)

        try:
            utils.ensure_api_is_reacheable(
                killswith_setting
            )
        except exceptions.APITimeoutError as e:
            raise Exception(
                "{}".format(e)
            )
        except exceptions.UnreacheableAPIError as e:
            raise Exception(
                "{}".format(e)
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception("{}".format(e))

    @staticmethod
    def ensure_internet_connection_is_available(killswith_setting):
        logger.info("Checking internet connectivity")
        if killswith_setting == KillswitchStatusEnum.HARD:
            return

        try:
            requests.get(
                "http://protonstatus.com/",
                timeout=5,
            )
        except requests.exceptions.Timeout as e:
            logger.exception("InternetConnectionError: {}".format(e))
            raise exceptions.InternetConnectionError(
                "No internet connection found, request timed out. "
                "Please make sure you are connected and retry."
            )
        except (requests.exceptions.RequestException, Exception) as e:
            logger.exception("InternetConnectionError: {}".format(e))
            raise exceptions.InternetConnectionError(
                "No internet connection. "
                "Please make sure you are connected and retry."
            )

    @staticmethod
    def ensure_api_is_reacheable(ks_status):
        logger.info("Checking API connectivity")

        if ks_status == KillswitchStatusEnum.HARD:
            return

        try:
            requests.get(
                "https://api.protonvpn.ch/tests/ping", timeout=10
            )
        except requests.exceptions.Timeout as e:
            logger.exception("APITimeoutError: {}".format(e))
            raise exceptions.APITimeoutError(
                "API unreacheable. Connection timed out."
            )
        except (requests.exceptions.RequestException, Exception) as e:
            logger.exception("UnreacheableAPIError: {}".format(e))
            raise exceptions.UnreacheableAPIError(
                "Couldn't reach Proton API."
                "This might happen due to connection issues or network blocks."
            )

    @staticmethod
    def ensure_servername_is_valid(servername):
        """Check if the provided servername is in a valid format.

        Args:
            servername (string): the servername [SE-PT#1]
        Returns:
            bool
        """
        logger.info("Validating servername")
        if not isinstance(servername, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(servername))
            logger.error(
                "[!] TypeError: {}. Raising Exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        re_compile = re.compile(r"^(\w\w)(-\w+)?#(\w+-)?(\w+)$")

        if not re_compile.search(servername):
            raise Exception(
                "IllegalServername: Invalid servername {}".format(
                    servername
                )
            )

    @staticmethod
    def ensure_ip_is_valid(ipaddr):
        """Check if the provided IP is valid IPv4.

        Args:
            ipaddr (string): IPv4

        Returns:
            bool
        """
        if not isinstance(ipaddr, str):
            raise ValueError("Invalid object type")

        valid_ip_re = re.compile(
            r'^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'
            r'(/(3[0-2]|[12][0-9]|[1-9]))?$'  # Matches CIDR
        )

        if not valid_ip_re.match(ipaddr):
            raise Exception(
                "Invalid IP address \"{}\"".format(
                    ipaddr
                )
            )

    @staticmethod
    def is_protocol_valid(protocol):
        logger.info("Checking if protocol is valid")
        try:
            protocol = ProtocolEnum(protocol)
        except (TypeError, ValueError):
            return False

        if protocol in FLAT_SUPPORTED_PROTOCOLS:
            return True

        return False

    @staticmethod
    def ensure_protocol_is_valid(protocol):
        """Check if provided protocol is a valid protocol.

        Args:
            protocol (ProtocolEnum)

        Returns:
            bool
        """
        logger.info("ensuring that protocol is valid")
        if not Utilities.is_protocol_valid(protocol):
            raise Exception(
                "Invalid protocol \"{}\"".format(
                    protocol
                )
            )

    @staticmethod
    def parse_user_input(
        user_input,
        ensure_country_exists,
        user_settings_protocol
    ):
        connection_type = user_input.get("connection_type")
        connection_type_extra_arg = user_input.get("connection_type_extra_arg")
        protocol = user_input.get("protocol")

        utils = Utilities
        if connection_type == ConnectionTypeEnum.COUNTRY:
            ensure_country_exists(connection_type_extra_arg)
        if connection_type == ConnectionTypeEnum.SERVERNAME:
            utils.ensure_servername_is_valid(
                connection_type_extra_arg
            )

        connection_type = connection_type
        connection_type_extra_arg = connection_type_extra_arg

        if connection_type not in [
            ConnectionTypeEnum.SERVERNAME, ConnectionTypeEnum.COUNTRY
        ]:
            connection_type_extra_arg = connection_type

        if not utils.is_protocol_valid(protocol):
            protocol = ProtocolEnum(
                user_settings_protocol
            )
        else:
            protocol = ProtocolEnum(protocol)

        return connection_type, connection_type_extra_arg, protocol

    @staticmethod
    def post_setup_connection_save_metadata(
        connection_metadata, servername,
        protocol, physical_server
    ):
        connection_metadata.save_servername(servername)
        connection_metadata.save_protocol(protocol)
        connection_metadata.save_display_server_ip(physical_server.exit_ip)
        connection_metadata.save_server_ip(physical_server.entry_ip)
