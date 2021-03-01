import json
import random
import re

from .. import exceptions
from ..constants import CACHED_SERVERLIST
from ..enums import FeatureEnum, UserSettingStatusEnum, ProtocolEnum, ConnectionTypeEnum
from ..logger import logger
from . import capture_exception
from .connection_state_manager import ConnectionStateManager


class ServerManager(ConnectionStateManager):
    killswitch_status = UserSettingStatusEnum.DISABLED
    CACHED_SERVERLIST = CACHED_SERVERLIST

    def __init__(self, cert_manager, user_manager):
        self.cert_manager = cert_manager
        self.user_manager = user_manager

    def generate_server_certificate(
        self, servername,
        server_feature, protocol,
        servers, filtered_servers
    ):
        """Generate server configuration.

        Args:
            servername (string): servername (ie PT#8, CH#6)
            server_feature (FeatureEnum): FeatureEnum object
            protocol (string): selected protocol
            servers (list): server list
            filtered_servers (list): filtered server list

        Returns:
            string: certificate filepath
        """
        self.validate_protocol(protocol)

        physical_server_list = self.get_physical_server_list(
            servername, servers, filtered_servers
        )
        physical_server = self.get_random_physical_server(
            physical_server_list
        )
        entry_IP, exit_IP = self.get_server_entry_exit_ip(
            physical_server
        )
        server_label = self.get_server_label(
            physical_server
        )

        domain = self.get_server_domain(physical_server)

        matching_domain = self.get_matching_domain(
            servers, exit_IP, server_feature
        )

        if matching_domain != None:
            domain = matching_domain

        logger.info("Saving servername: \"{}\"".format(servername))
        self.save_servername(servername)

        logger.info("Saving protocol: \"{}\"".format(protocol))
        self.save_protocol(protocol)

        logger.info("Saving server entry IP: \"{}\"".format(entry_IP))
        self.save_server_ip(entry_IP)

        logger.info("Saving server exit IP: \"{}\"".format(exit_IP))
        self.save_display_server_ip(exit_IP)

        return self.cert_manager.generate_vpn_cert(
            protocol, servername, [entry_IP], exit_IP
        ), domain, [entry_IP], server_label

    def get_config_for_fastest_server(self, _=None):
        """Get configuration for fastest server.

        Returns:
            tuple
        """
        logger.info("Generating config for fastest server")
        servers = self.extract_server_list()

        excluded_features = [
            FeatureEnum.SECURE_CORE,
            FeatureEnum.TOR,
            FeatureEnum.P2P
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

        return self.get_fastest_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_config_for_fastest_server_in_country(self, country_code):
        """Get configuration for fastest server in a specific country.

        Args:
            country_code (string): country code [PT|SE|CH ...]

        Returns:
            tuple
        """
        logger.info("Generating config for fastest server in \"{}\"".format(
            country_code
        ))
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

    def get_config_for_specific_server(self, servername):
        """Get configuration to specified server.

        Args:
            servername (string): servername to connect

        Returns:
            tuple
        """
        if isinstance(servername, list):
            servername = servername[1]

        try:
            servername = servername.upper()
        except AttributeError:
            raise ValueError(
                "Expected string for servername (not {})".format(
                    type(servername)
                )
            )

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
        self, feature
    ):
        """Get configuration to fastest server based on specified feature.

        Args:
            feature (ConnectionTypeEnum)

        Returns:
            tuple
        """
        servers = self.extract_server_list()

        allowed_features = {
            "none": FeatureEnum.NORMAL,
            ConnectionTypeEnum.SECURE_CORE: FeatureEnum.SECURE_CORE,
            ConnectionTypeEnum.TOR: FeatureEnum.TOR,
            ConnectionTypeEnum.PEER2PEER: FeatureEnum.P2P,
            "to-add-streaming": FeatureEnum.STREAMING,
            "to-add-ipv6": FeatureEnum.IPv6
        }

        if feature not in allowed_features:
            logger.exception("[!] Feature is non-existent error: {}".format(
                feature
            ))
            raise ValueError("Feature is non-existent")

        feature = allowed_features[feature]
        filtered_servers = self.filter_servers(
            servers,
            include_features=[feature],
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

    def get_config_for_random_server(self, _=None):
        """Get configuration to random server.

        Returns:
            tuple
        """
        servers = self.extract_server_list()

        filtered_servers = self.filter_servers(servers)

        # Add new element to tuple
        return self.get_random_server(
            filtered_servers
        ) + (filtered_servers, servers)

    def get_physical_server_list(self, servername, servers, filtered_servers):
        """Get physical servers for matching logical servername.

        Args:
            servername (string): servername (ie PT#8, CH#6)
            servers (list): server list
            filtered_servers (list): filtered server list

        Returns:
            list(dict): contains list of physical servers
        """
        try:
            physical_servers = self.extract_server_value(
                servername, "Servers", servers
            )
        except IndexError as e:
            logger.info("[!] IndexError: {}".format(e))
            raise IndexError(e)
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)
            raise Exception("Unknown exception: {}".format(e))

        return physical_servers

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

        return None

    def validate_protocol(self, protocol):
        """Validates protocol.

        Args:
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
        """
        logger.info("Validating protocol")
        if not isinstance(protocol, ProtocolEnum):
            err_msg = "Incorrect object type, "\
                "ProtocolEnum is expected but got {} instead".format(
                    type(protocol)
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise TypeError(err_msg)

    def get_random_physical_server(self, physical_server_list):
        """Get physical server at random.

        Args:
            physical_server_list (list(dict)): list with physical servers

        Return:
            dict: with server information
        """
        logger.info("Selecting random physical server")
        enabled_servers = [
            server
            for server
            in physical_server_list
            if server["Status"] == 1
        ]

        if len(enabled_servers) == 0:
            logger.error("List of physical servers is empty")
            raise exceptions.EmptyServerListError("No servers could be found")

        return random.choice(enabled_servers)

    def get_server_label(self, physical_server):
        """Get physical server label.

        Args:
            server_physical_list (list(dict)): physical server
        Returns:
            None|Label: Returns the label if the key exists and it's length
            is greater then 0, else return None.
        """
        server_label = physical_server.get("Label", "").strip()

        return server_label or None

    def get_server_domain(self, physical_server):
        """Get physical server domain name.

        Args:
            physical_server (dict): physical server

        Returns:
            string
        """
        return physical_server.get("Domain")

    def get_server_entry_exit_ip(self, physical_server):
        """Get physical IPs from sub-servers.

        Args:
            physical_server (dict): physical server

        Returns:
            tuple: (entry_IP, exit_IP)
        """
        logger.info("Getting entry/exit IPs")

        return physical_server.get("EntryIP"), physical_server.get("ExitIP")

    def filter_servers(
        self, servers,
        exclude_features=None, include_features=None,
        connect_to_country=None, servername=None
    ):
        """Filter servers based specified input.

        Args:
            servers (list(dict)): a list containing raw servers info
            exclude_features (list): [FeatureEnum.TOR, ...] (optional)
            include_features (list): [FeatureEnum.TOR, ...] (optional)
                exclude_features and include_features are mutually exclusive.
            connect_to_country (string): country code PT|SE|CH (optional)
            servername (string): servername PT#1|SE#5|CH#10 (optional)

        Returns:
            list: serverlist extracted from raw json
        """
        logger.info("Filtering servers")
        user_tier = self.fetch_user_tier()
        if (
            exclude_features and include_features
            or exclude_features != None and include_features != None
        ):
            raise ValueError(
                "Pass features to either exclude or "
                "include, but not both."
            )

        filtered_servers = []
        for server in servers:
            server_feature = FeatureEnum(server["Features"] or 0)
            if (
                server["Tier"] <= user_tier
            ) and (
                server["Status"] == 1
            ) and (
                (
                    not exclude_features
                    and not include_features
                ) or (
                    exclude_features
                    and server_feature not in exclude_features
                ) or (
                    include_features
                    and server_feature in include_features
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
        """Extracts server list from raw cache file.

        Returns:
            list
        """
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
            tuple: same output as from get_random_server()
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
            tuple: (
                servername(string),
                server_feature(string),
                server_feature(FeatureEnum)
            )
        """
        random_server = random.choice(server_pool)
        servername = random_server["Name"]
        server_feature = 0
        random_server_feature = random_server["Features"] or 0
        server_feature = FeatureEnum(int(random_server_feature))

        return servername, server_feature

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

        re_compile = re.compile(r"^(\w\w)(-\w+)?#(\w+-)?(\w+)$")

        return False if not re_compile.search(servername) else True
