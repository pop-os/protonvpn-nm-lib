import json
import random
import re

from .. import exceptions
from ..constants import CACHED_SERVERLIST
from ..enums import FeatureEnum, UserSettingStatusEnum, KillswitchStatusEnum
from ..logger import logger
from . import capture_exception
from .connection_state_manager import ConnectionStateManager


class ServerManager(ConnectionStateManager):
    REFRESH_INTERVAL = 15
    killswitch_status = UserSettingStatusEnum.DISABLED

    def __init__(self, cert_manager, user_manager):
        self.cert_manager = cert_manager
        self.user_manager = user_manager

    def fastest(self, session, protocol, *_):
        """Connect to fastest server.

        Args:
            session (proton.api.Session): current user session
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        logger.info("Generating data for fastest connect")
        self.validate_session_protocol(session, protocol)
        if not self.killswitch_status == KillswitchStatusEnum:
            session.cache_servers()

        servers = self.extract_server_list()
        excluded_features = [
            FeatureEnum.SECURE_CORE, FeatureEnum.TOR, FeatureEnum.P2P
        ]
        filtered_servers = self.filter_servers(
            session, servers, exclude_features=excluded_features
        )
        servername, domain, server_feature = self.get_fastest_server(
            filtered_servers
        )

        entry_IP, exit_IP = self.get_connection_ips(
            servername, servers, filtered_servers
        )

        try:
            domain = self.get_matching_domain(servers, exit_IP, server_feature)
        except KeyError:
            pass

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, entry_IP
        ), domain, entry_IP

    def country_f(self, session, protocol, *args):
        """Connect to fastest server in a specific country.

        Args:
            session (proton.api.Session): current user session
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
            args (tuple(list)): country code [PT|SE|CH]
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        self.validate_session_protocol(session, protocol)
        if not isinstance(args, tuple):
            err_msg = "Incorrect object type, "\
                "tuple is expected but got {} instead".format(type(args))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)
        elif not isinstance(args[0], list):
            err_msg = "Incorrect object type, "\
                "list is expected but got {} instead".format(type(args[0]))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        try:
            country_code = args[0][1].strip().upper()
        except IndexError as e:
            logger.exception("[!] IndexError: {}".format(e))
            raise IndexError(
                "Incorrect object type, "
                + "tuple(list) is expected but got {} ".format(args)
                + "instead"
            )
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)

        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()
        excluded_features = [
            FeatureEnum.TOR, FeatureEnum.SECURE_CORE
        ]
        filtered_servers = self.filter_servers(
            session,
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

        servername, domain, server_feature = self.get_fastest_server(
            filtered_servers
        )

        entry_IP, exit_IP = self.get_connection_ips(
            servername, servers, filtered_servers
        )

        try:
            domain = self.get_matching_domain(servers, exit_IP, server_feature)
        except KeyError:
            pass

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, entry_IP
        ), domain, entry_IP

    def direct(self, session, protocol, *args):
        """Connect directly to specified server.

        Args:
            session (proton.api.Session): current user session
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
            args (tuple(list)|tuple): servername to connect to
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        self.validate_session_protocol(session, protocol)
        if not isinstance(args, tuple):
            err_msg = "Incorrect object type, "\
                "tuple is expected but got {} "\
                "instead".format(type(args))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)
        elif (
            isinstance(args, tuple) and len(args) == 0
        ) or (
            isinstance(args, str) and len(args) == 0
        ):
            err_msg = "The provided argument \"args\" is empty"
            logger.error(
                "[!] ValueError: {}. Raising exception.".format(err_msg)
            )
            raise ValueError(err_msg)

        user_input = args[0]
        # This check is done since when a user uses the dialog
        # the input passed diferently, thus it needs to be checked.
        if isinstance(user_input, list):
            user_input = user_input[1]

        servername = user_input.strip().upper()

        if not self.is_servername_valid(user_input):
            err_msg = "Invalid servername {}".format(user_input)
            logger.error(
                "[!] IllegalServername: {}. Raising exception.".format(err_msg)
            )
            raise exceptions.IllegalServername(err_msg)

        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()
        filtered_servers = self.filter_servers(
            session,
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

        entry_IP, exit_IP = self.get_connection_ips(
            servername, servers, filtered_servers
        )

        servername, domain, server_feature = self.get_random_server(
            filtered_servers
        )

        try:
            domain = self.get_matching_domain(servers, exit_IP, server_feature)
        except KeyError:
            pass

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, entry_IP
        ), domain, entry_IP

    def feature_f(self, session, protocol, *args):
        """Connect to fastest server based on specified feature.

        Args:
            session (proton.api.Session): current user session
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
            args (tuple(list)): literal feature [p2p|tor|sc]
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        self.validate_session_protocol(session, protocol)
        if not isinstance(args, tuple):
            err_msg = "Incorrect object type, "\
                "tuple is expected but got {} "\
                "instead".format(type(args))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)
        elif len(args) == 0:
            err_msg = "The provided argument \"args\" is empty"
            logger.error(
                "[!] ValueError: {}. Raising exception.".format(err_msg)
            )
            raise ValueError(err_msg)
        elif not isinstance(args[0], list):
            err_msg = "Incorrect object type, "\
                "list is expected but got {} "\
                "instead".format(type(args))
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        literal_feature = args[0][0].strip().lower()
        allowed_features = {
            "normal": FeatureEnum.NORMAL,
            "sc": FeatureEnum.SECURE_CORE,
            "tor": FeatureEnum.TOR,
            "p2p": FeatureEnum.P2P,
            "stream": FeatureEnum.STREAMING,
            "ipv6": FeatureEnum.IPv6
        }

        try:
            feature = allowed_features[literal_feature]
        except KeyError as e:
            logger.exception("[!] ValueError: {}".format(e))
            raise ValueError("Feature is non-existent")
        except Exception as e:
            logger.exception("[!] Unknown exception: {}".format(e))
            capture_exception(e)

        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()
        filtered_servers = self.filter_servers(
            session,
            servers,
            # exclude all other features except the selected one
            exclude_features=[
                v
                for k, v in allowed_features.items()
                if not feature == v
            ]
        )

        if len(filtered_servers) == 0:
            err_msg = "No servers found with the {} feature".format(
                literal_feature
            )
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        servername, domain, server_feature = self.get_fastest_server(
            filtered_servers
        )

        entry_IP, exit_IP = self.get_connection_ips(
            servername, servers, filtered_servers
        )

        try:
            domain = self.get_matching_domain(servers, exit_IP, server_feature)
        except KeyError:
            pass

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, entry_IP
        ), domain, entry_IP

    def random_c(self, session, protocol, *_):
        """Connect to a random server.

        Args:
            session (proton.api.Session): current user session
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        self.validate_session_protocol(session, protocol)
        if not self.killswitch_status == KillswitchStatusEnum.HARD:
            session.cache_servers()
        servers = self.extract_server_list()
        filtered_servers = self.filter_servers(session, servers)

        servername, domain, server_feature = self.get_random_server(
            filtered_servers
        )

        entry_IP, exit_IP = self.get_connection_ips(
            servername, servers, filtered_servers
        )

        try:
            domain = self.get_matching_domain(servers, exit_IP, server_feature)
        except KeyError:
            pass

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, entry_IP
        ), domain, entry_IP

    def get_connection_ips(self, servername, servers, filtered_servers):
        try:
            entry_IP, exit_IP = self.generate_ip_list(
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
        _list = [FeatureEnum.NORMAL, FeatureEnum.SECURE_CORE]

        if server_feature in _list:
            for server in server_pool:
                for physical_server in server["Servers"]:
                    if exit_IP in physical_server["EntryIP"]:
                        return physical_server["Domain"]
        else:
            raise KeyError("No such server")

    def validate_session_protocol(self, session, protocol):
        """Validates session and protocol

        Args:
            session (proton.api.Session): current user session
            protocol (ProtocolEnum): ProtocolEnum.TCP, ProtocolEnum.UDP ...
        """
        logger.info("Validating session and protocol")
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

    def generate_ip_list(
        self, servername, servers,
        server_certificate_check=True
    ):
        """Exctract IPs from server list, based on servername.

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
        self, session, servers,
        exclude_features=None, connect_to_country=None, servername=None
    ):
        """Filter servers based specified input.

        Args:
            session (proton.api.Session): current user session
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
        try:
            with open(CACHED_SERVERLIST, "r") as f:
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
        """Get user tier.

        Returns:
            int: current user session tier
        """
        return self.user_manager.tier

    def get_fastest_server(self, server_pool):
        """Get fastest server from a list of servers.

        Args:
            server_pool (list): pool with servers
        Returns:
            string: servername with the highest score (fastest)
        """
        logger.info("Getting fastest server")

        if not isinstance(server_pool, list):
            err_msg = "Incorrect object type, "\
                "list is expected but got {} instead".format(
                    type(server_pool)
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)

        # Sort servers by "speed" and select top n according to pool_size
        fastest_pool = sorted(
            server_pool, key=lambda server: server["Score"]
        )
        if len(fastest_pool) >= 50:
            pool_size = 4
        else:
            pool_size = 1

        return self.get_random_server(fastest_pool[:pool_size])

    def get_random_server(self, server_pool):
        """Get a random server from a server pool.

        Args:
            server_pool (list): logical servers
        Returns:
            tuple: (servername, domain, if_selected_server_is_secure_core)
        """
        random_server = random.choice(server_pool)
        fastest_server_name = random_server["Name"]
        fastest_server_domain = random_server["Domain"]
        # is_secure_core = True if random_server["Features"] == 1 else False
        server_feature = random_server["Features"]

        return (fastest_server_name, fastest_server_domain, server_feature)

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
