import json
import random
import re

from .. import exceptions
from ..constants import CACHED_SERVERLIST
from ..enums import FeatureEnum, UserSettingStatusEnum, KillswitchStatusEnum
from ..logger import logger
from . import capture_exception
from .connection_state_manager import ConnectionStateManager
from .proton_session_wrapper import ProtonSessionWrapper


class ServerManager(ConnectionStateManager):
    killswitch_status = UserSettingStatusEnum.DISABLED
    CACHED_SERVERLIST = CACHED_SERVERLIST

    def __init__(self, cert_manager, user_manager):
        self.cert_manager = cert_manager
        self.user_manager = user_manager

    def generate_server_certificate(
        self, servername, domain,
        server_feature, protocol,
        servers, filtered_servers
    ):
        """Generate server configuration.

        Args:
            servername (string): servername (ie PT#8, CH#6)
            domain (string): server domain
            server_feature (FeatureEnum): FeatureEnum object
            protocol (string): selected protocol
            servers (list): server list
            filtered_servers (list): filtered server list
        Returns:
            string: certificate filepath
        """
        self.validate_protocol(protocol)

        entry_IP, exit_IP = self.get_server_entry_exit_ip(
            servername, servers, filtered_servers
        )

        try:
            matching_domain = self.get_matching_domain(
                servers, exit_IP, server_feature
            )
        except KeyError:
            matching_domain = domain

        return self.cert_manager.generate_vpn_cert(
            protocol, servername, entry_IP
        ), matching_domain, entry_IP

    def get_config_for_fastest_server(self, session, _=None):
        """Get configuration for fastest server.

        Args:
            session (ProtonSessionWrapper): current user session object
        Returns:
            tuple: (
                servername, server_domain, server_feature,
                filtered_servers, servers
            )
        """
        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()

        excluded_features = [
            FeatureEnum.SECURE_CORE, FeatureEnum.TOR, FeatureEnum.P2P
        ]
        filtered_servers = self.filter_servers(
            servers, exclude_features=excluded_features
        )
        if len(filtered_servers) == 0:
            err_msg = "No available servers could be found."
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        # Add new element to tuple
        return self.get_fastest_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_config_for_fastest_server_in_country(self, session, country_code):
        """Get configuration for fastest server in a specific country.

        Args:
            session (ProtonSessionWrapper): current user session object
            country_code (string): country code [PT|SE|CH ...]
        Returns:
            tuple: (
                servername, server_domain, server_feature,
                filtered_servers, servers
            )
        """
        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()

        excluded_features = [
            FeatureEnum.TOR, FeatureEnum.SECURE_CORE
        ]
        filtered_servers = self.filter_servers(
            servers,
            exclude_features=excluded_features,
            connect_to_country=country_code
        )

        if len(filtered_servers) == 0:
            err_msg = "No available servers could be found for \"{}\".".format(
                country_code
            )
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        # Add new element to tuple
        return self.get_fastest_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_config_for_specific_server(self, session, servername):
        """Get configuration to specified server.

        Args:
            session (ProtonSessionWrapper): current user session object
            servername (string): servername to connect
        Returns:
            tuple: (
                servername, server_domain, server_feature,
                filtered_servers, servers
            )
        """
        # This check is done since when a user uses the dialog
        # the input passed diferently, thus it needs to be checked.
        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()

        if isinstance(servername, list):
            servername = servername[1]

        servername = servername.strip().upper()

        if not self.is_servername_valid(servername):
            err_msg = "Invalid servername {}".format(servername)
            logger.error(
                "[!] IllegalServername: {}. Raising exception.".format(err_msg)
            )
            raise exceptions.IllegalServername(err_msg)

        servers = self.extract_server_list()
        filtered_servers = self.filter_servers(
            servers,
            servername=servername
        )

        if len(filtered_servers) == 0:
            err_msg = "No available servers could be found for \"{}\"".format(
                servername
            )
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        # Add new element to tuple
        return self.get_random_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_config_for_fastest_server_with_specific_feature(
        self, session, feature
    ):
        """Get configuration to fastest server based on specified feature.

        Args:
            session (ProtonSessionWrapper): current user session object
            feature (string): literal feature [p2p|tor|sc]
        Returns:
            tuple: (
                servername, server_domain, server_feature,
                filtered_servers, servers
            )
        """
        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()

        allowed_features = {
            "normal": FeatureEnum.NORMAL,
            "sc": FeatureEnum.SECURE_CORE,
            "tor": FeatureEnum.TOR,
            "p2p": FeatureEnum.P2P,
            "stream": FeatureEnum.STREAMING,
            "ipv6": FeatureEnum.IPv6
        }

        if feature not in allowed_features:
            logger.exception("[!] Feature is non-existent error: {}".format(
                feature
            ))
            raise ValueError("Feature is non-existent")

        # exclude all other features except the selected one
        filtered_servers = self.filter_servers(
            servers,
            exclude_features=[
                v
                for k, v in allowed_features.items()
                if not allowed_features[feature] == v
            ]
        )

        if len(filtered_servers) == 0:
            err_msg = "No servers found with the {} feature".format(
                feature
            )
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        # Add new element to tuple
        return self.get_fastest_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_config_for_random_server(self, session, _=None):
        """Get configuration to random server.

        Args:
            session (ProtonSessionWrapper): current user session object
        Returns:
            tuple: (
                servername, server_domain, server_feature,
                filtered_servers, servers
            )
        """
        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()

        filtered_servers = self.filter_servers(servers)

        # Add new element to tuple
        return self.get_random_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_server_entry_exit_ip(self, servername, servers, filtered_servers):
        """Get server entry and exit IP.

        Args:
            servername (string): servername (ie PT#8, CH#6)
            servers (list): server list
            filtered_servers (list): filtered server list
        Returns:
            tuple: (entry_IP, exit_IP)
        """
        try:
            entry_IP, exit_IP = self.get_pyshical_ip_list(
                servername, filtered_servers
            )
        except IndexError as e:
            logger.exception("[!] IllegalServername: {}".format(e))
            raise exceptions.IllegalServername(
                "\"{}\" is not a valid server".format(servername)
            )
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)
        else:
            self.save_server_ip(entry_IP)
            return entry_IP, exit_IP

    def get_matching_domain(self, server_pool, exit_IP, server_feature):
        """Get matching domaing for featureless or secure-core servers.

        Args:
            server_pool (list): pool with logical servers
            exit_IP (string): server exit IP
            server_feature (FeatureEnum): FeatureEnum object
        Returns:
            string: matching server domain
        """
        _list = [FeatureEnum.NORMAL, FeatureEnum.SECURE_CORE]

        if server_feature in _list:
            for server in server_pool:
                for physical_server in server["Servers"]:
                    if exit_IP in physical_server["EntryIP"]:
                        return physical_server["Domain"]
        else:
            raise KeyError("No such server")

    def validate_session(self, session):
        """Validates session.

        Args:
            session (proton.api.Session): current user session
        """
        logger.info("Validating session")
        if not isinstance(session, ProtonSessionWrapper):
            err_msg = "Incorrect object type, "\
                "{} is expected "\
                "but got {} instead".format(
                    ProtonSessionWrapper, session
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise TypeError(err_msg)

    def validate_protocol(self, protocol):
        """Validates protocol.

        Args:
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
        """
        logger.info("Validating protocol")
        if not isinstance(protocol, str):
            err_msg = "Incorrect object type, "\
                "str is expected but got {} instead".format(type(protocol))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise TypeError(err_msg)
        elif len(protocol) == 0:
            err_msg = "The provided argument \"protocol\" is empty"
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise ValueError(err_msg)

    def get_pyshical_ip_list(
        self, servername, servers,
        server_certificate_check=True
    ):
        """Get physical IPs from server list, based on servername.

        Args:
            servername (string): servername [PT#1]
            servers (list): curated list containing the servers
        Returns:
            list: IPs for the selected server
        """
        logger.info("Generating IP list")

        try:
            subservers = self.extract_server_value(
                servername, "Servers", servers
            )
        except IndexError as e:
            logger.info("[!] IndexError: {}".format(e))
            raise IndexError(e)
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)

        ip_list = [
            (subserver["EntryIP"], subserver["ExitIP"])
            for subserver
            in subservers
            if subserver["Status"] == 1
        ]
        entry_IP, exit_IP = random.choice(ip_list)

        return [entry_IP], exit_IP

    def filter_servers(
        self, servers,
        exclude_features=None, connect_to_country=None, servername=None
    ):
        """Filter servers based specified input.

        Args:
            servers (list(dict)): a list containing raw servers info
            exclude_features (list): [FeatureEnum.TOR, ...] (optional)
            connect_to_country (string): country code PT|SE|CH (optional)
            servername (string): servername PT#1|SE#5|CH#10 (optional)
        Returns:
            list: serverlist extracted from raw json
        """
        logger.info("Filtering servers")
        user_tier = self.fetch_user_tier()

        filtered_servers = []
        for server in servers:
            if (
                server["Tier"] <= user_tier
            ) and (
                server["Status"] == 1
            ) and (
                (
                    not exclude_features
                ) or (
                    exclude_features
                    and server["Features"] not in exclude_features
                )
            ) and (
                (
                    not connect_to_country
                ) or (
                    connect_to_country
                    and server["ExitCountry"] == connect_to_country
                )
            ) and (
                (
                    not servername
                ) or (
                    servername
                    and server["Name"] == servername
                )
            ):
                filtered_servers.append(server)

        return filtered_servers

    def extract_server_list(self):
        """Extracts server list from raw cache file."""
        try:
            with open(self.CACHED_SERVERLIST, "r") as f:
                server_data = json.load(f)
        except FileNotFoundError as e:
            killswitch_msg = ""
            if not self.killswitch_status == UserSettingStatusEnum.DISABLED:
                killswitch_msg = "Killswitch is enabled, "\
                    "please first disable killswitch to cache servers"

            logger.exception(
                "[!] MissingCacheError: {}. {}".format(e, killswitch_msg)
            )
            raise exceptions.MissingCacheError(
                "Server cache not found. {}".format(killswitch_msg)
            )

        return server_data["LogicalServers"]

    def fetch_user_tier(self):
        """Fetch user tier.

        Returns:
            int: current user session tier
        """
        return self.user_manager.tier

    def get_fastest_server(self, filtered_servers):
        """Get fastest server.

        Args:
            filtered_servers (list): filtered servers
        Returns:
            string: servername with the highest score (fastest)
        """
        logger.info("Getting fastest server")

        if not isinstance(filtered_servers, list):
            err_msg = "Incorrect object type, "\
                "list is expected but got {} instead".format(
                    type(filtered_servers)
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        # Sort servers by "speed" and select top n according to pool_size
        fastest_pool = sorted(
            filtered_servers, key=lambda server: server["Score"]
        )
        if len(fastest_pool) >= 50:
            pool_size = 4
        else:
            pool_size = 1

        return self.get_random_server(fastest_pool[:pool_size])

    def get_random_server(self, server_pool):
        """Get a random server from a server pool.

        Args:
            server_pool (list): pool with logical servers
        Returns:
            tuple: (servername, domain, server_feature)
        """
        random_server = random.choice(server_pool)
        servername = random_server["Name"]
        server_domain = random_server["Domain"]
        server_feature = random_server["Features"]

        return servername, server_domain, server_feature

    def extract_server_value(
        self, servername,
        key, servers
    ):
        """Extract server data based on servername.

        Args:
            servername (string): servername [PT#1]
            key (string): keyword that contains servernames in json
            servers (list): a list containing the servers
        Returns:
            list: dict with server information
        """
        for server in servers:
            if server["Name"] == servername and server["Status"]:
                return server[key]

        raise IndexError

    def extract_country_name(self, code):
        """Extract country name based on specified code.

        Args:
            code (string): country code [PT|SE|CH]
        Returns:
            string:
                country name if found, else returns country code
        """
        from ..country_codes import country_codes
        return country_codes.get(code, code)

    def is_servername_valid(self, servername):
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

        servername = servername.upper()

        re_short = re.compile(r"^((\w\w)(-|#)?(\d{1,3})-?(TOR)?)$")
        # For long format (IS-DE-01 | Secure-Core/Free/US Servers)
        re_long = re.compile(
            r"^(((\w\w)(-|#)?([A-Z]{2}|FREE))(-|#)?(\d{1,3})-?(TOR)?)$"
        )
        return_servername = False

        if re_short.search(servername):
            user_server = re_short.search(servername)

            country_code = user_server.group(2)
            number = user_server.group(4).lstrip("0")
            tor = user_server.group(5)
            servername = "{0}#{1}".format(country_code, number)
            return_servername = servername + "{0}".format(
                '-' + tor if tor is not None else ''
            )

        elif re_long.search(servername):
            user_server = re_long.search(servername)
            country_code = user_server.group(3)
            country_code2 = user_server.group(5)
            number = user_server.group(7).lstrip("0")
            tor = user_server.group(8)
            return_servername = "{0}-{1}#{2}".format(
                country_code, country_code2, number
            ) + "{0}".format(
                '-' + tor if tor is not None else ''
            )

        return False if not return_servername else True
