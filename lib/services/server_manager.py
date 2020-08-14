import datetime
import re
import json
import random
import os
from lib.constants import CACHED_SERVERLIST, PROTON_XDG_CACHE_HOME
from lib import exceptions
from proton.api import Session


class ServerManager():
    def __init__(self, cert_manager):
        self.cert_manager = cert_manager

    def fastest(self, session, protocol, *_):
        """Connect to the fastest server.

        Args:
            session (proton.api.Session): current user session
            protocol (string): protocol to be used
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        if not isinstance(session, Session):
            raise TypeError(
                "Incorrect object type, "
                + "{} is expected ".format(type(Session))
                + "but got {} instead".format(type(protocol))
            )

        if not isinstance(protocol, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(protocol))
            )

        self.pull_server_data(session)

        servers = self.get_servers(session)
        # ProtonVPN Features: 1: SECURE-CORE, 2: TOR, 4: P2P, 8: Streaming
        excluded_features = [1, 2]

        # Filter out excluded features
        server_pool = []
        for server in servers:
            if server["Features"] not in excluded_features:
                server_pool.append(server)

        servername = self.get_fastest_server(server_pool)

        try:
            ip_list = self.get_ip_list(servername, servers)
        except IndexError:
            raise exceptions.IllegalServername(
                "\"{}\" is not a valid server".format(servername)
            )

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, ip_list
        )

    def country_f(self, session, protocol, *args):
        """Connect to the fastest server in a specific country.

        Args:
            session (proton.api.Session): current user session
            protocol (string): protocol to be used
            args (tuple(list)): country code [PT|SE|CH]
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        if not isinstance(session, Session):
            raise TypeError(
                "Incorrect object type, "
                + "{} is expected ".format(type(Session))
                + "but got {} instead".format(type(protocol))
            )

        if not isinstance(protocol, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(protocol))
            )

        country_code = args[0][1].strip().upper()
        self.pull_server_data(session)
        servers = self.get_servers(session)

        # ProtonVPN Features: 1: SECURE-CORE, 2: TOR, 4: P2P
        excluded_features = [1, 2]

        # Filter out excluded features and countries
        server_pool = []
        for server in servers:
            if (
                server["Features"] not in excluded_features
            ) and (
                server["ExitCountry"] == country_code
            ):
                server_pool.append(server)

        if len(server_pool) == 0:
            raise Exception(
                "Invalid country code \"{}\"".format(country_code)
            )

        servername = self.get_fastest_server(server_pool)

        try:
            ip_list = self.get_ip_list(servername, servers)
        except IndexError:
            raise exceptions.IllegalServername(
                "\"{}\" is not a valid server".format(servername)
            )

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, ip_list
        )

    def direct(self, session, protocol, *args):
        """Connect to a single given server directly.

        Args:
            session (proton.api.Session): current user session
            protocol (string): protocol to be used
            args (tuple(list)|list): servername to connect to
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        if not isinstance(session, Session):
            raise TypeError(
                "Incorrect object type, "
                + "{} is expected ".format(type(Session))
                + "but got {} instead".format(type(protocol))
            )

        if not isinstance(protocol, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(protocol))
            )

        user_input = args[0]
        if isinstance(user_input, list):
            user_input = user_input[1]

        servername = user_input.strip().upper()

        if not self.is_servername_valid(user_input):
            raise exceptions.IllegalServername(
                "Unexpected servername"
            )

        servername = user_input
        self.pull_server_data(session)
        servers = self.get_servers(session)

        try:
            ip_list = self.get_ip_list(servername, servers)
        except IndexError:
            raise exceptions.IllegalServername(
                "\"{}\" is not an existing server".format(servername)
            )

        if servername not in [server["Name"] for server in servers]:
            raise Exception(
                "{} is either invalid, under maintenance ".format(servername)
                + "or inaccessible with your plan"
            )

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, ip_list
        )

    def feature_f(self, session, protocol, *args):
        """Connect to the fastest server based on specified feature.

        Args:
            session (proton.api.Session): current user session
            protocol (string): protocol to be used
            args (tuple(list)): literal feature to be used [p2p|tor|sc]
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        if not isinstance(session, Session):
            raise TypeError(
                "Incorrect object type, "
                + "{} is expected ".format(type(Session))
                + "but got {} instead".format(type(protocol))
            )

        if not isinstance(protocol, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(protocol))
            )

        literal_feature = args[0][0].strip().lower()
        allowed_features = {
            "sc": 1, "tor": 2,
            "p2p": 4, "stream": 8,
            "ipv6": 16
        }

        try:
            feature = allowed_features[literal_feature]
        except KeyError:
            raise Exception("Feature is non-existent")

        self.pull_server_data(session)

        servers = self.get_servers(session)

        server_pool = [s for s in servers if s["Features"] == feature]

        if len(server_pool) == 0:
            raise Exception(
                "No servers found with the {} feature".format(literal_feature)
            )

        servername = self.get_fastest_server(server_pool)

        try:
            ip_list = self.get_ip_list(servername, servers)
        except IndexError:
            raise exceptions.IllegalServername(
                "\"{}\" is not a valid server".format(servername)
            )

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, ip_list
        )

    def random_c(self, session, protocol, *_):
        """Connect to a random server.

        Args:
            session (proton.api.Session): current user session
            protocol (string): protocol to be used
        Returns:
            string: path to certificate file that is to be imported into nm
        """
        if not isinstance(session, Session):
            raise TypeError(
                "Incorrect object type, "
                + "{} is expected ".format(type(Session))
                + "but got {} instead".format(type(protocol))
            )

        if not isinstance(protocol, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(protocol))
            )

        servers = self.get_servers(session)

        servername = random.choice(servers)["Name"]

        try:
            ip_list = self.get_ip_list(servername, servers)
        except IndexError:
            raise exceptions.IllegalServername(
                "\"{}\" is not a valid server".format(servername)
            )

        return self.cert_manager.generate_vpn_cert(
            protocol, session,
            servername, ip_list
        )

    def pull_server_data(
        self, session,
        force=False, cached_serverlist=CACHED_SERVERLIST
    ):
        """Cache server data from API.

        Args:
            session (proton.api.Session): the current user session
            cached_serverlist (string): path to cached server list
            force (bool): wether refresh interval shuld be ignored or not
        """
        refresh_interval = 45

        if not isinstance(cached_serverlist, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(
                    type(cached_serverlist)
                )
            )

        if isinstance(cached_serverlist, str) and len(cached_serverlist) == 0:
            raise FileNotFoundError("No such file exists")

        if os.path.isdir(cached_serverlist):
            raise IsADirectoryError(
                "Provided file path is a directory, while file path expected"
            )

        if not os.path.isdir(PROTON_XDG_CACHE_HOME):
            os.mkdir(PROTON_XDG_CACHE_HOME)

        try:
            last_modified_time = datetime.datetime.fromtimestamp(
                os.path.getmtime(cached_serverlist)
            )
        except FileNotFoundError:
            last_modified_time = datetime.datetime.now()

        now_time = datetime.datetime.now()
        time_ago = now_time - datetime.timedelta(minutes=refresh_interval)

        if (
            not os.path.isfile(cached_serverlist)
        ) or (
            time_ago > last_modified_time or force
        ):

            data = session.api_request(endpoint="/vpn/logicals")

            with open(cached_serverlist, "w") as f:
                json.dump(data, f)

    def get_ip_list(self, servername, servers):
        """Exctracts the IP from the server list, based on servername.

        Args:
            servername (string): servername [PT#1]
            servers (list): a curated list containing the servers
        Returns:
            list: the ips for the selected server
        """
        try:
            subservers = self.get_server_value(servername, "Servers", servers)
        except IndexError as e:
            raise IndexError(e)
        ip_list = [subserver["EntryIP"] for subserver in subservers]

        return ip_list

    def get_servers(self, session):
        """Return a list of all servers based on tier.

        Args:
            session (proton.api.Session): the current user session
        Returns:
            list: the serverlist extracted from raw json, based on user tier
        """

        with open(CACHED_SERVERLIST, "r") as f:
            server_data = json.load(f)

        user_tier = self.get_user_tier(session)

        servers = server_data["LogicalServers"]

        # Sort server IDs by Tier
        return [server for server in servers if server["Tier"] <= user_tier and server["Status"] == 1] # noqa

    def get_user_tier(self, session):
        """Feches a users tier from the API.

        Args:
            session (proton.api.Session): the current user session
        Returns:
            int: current user session tier
        """
        data = session.api_request(endpoint="/vpn")
        return data["VPN"]["MaxTier"]

    def get_fastest_server(self, server_pool):
        """Return the fastest server from a list of servers.

        Args:
            server_pool (list): a pool with servers
        Returns:
            string: The servername with the highest score (fastest)
        """
        if not isinstance(server_pool, list):
            raise TypeError(
                "Incorrect object type, "
                + "list is expected but got {} instead".format(
                    type(server_pool)
                )
            )

        # Sort servers by "speed" and select top n according to pool_size
        fastest_pool = sorted(
            server_pool, key=lambda server: server["Score"]
        )
        if len(fastest_pool) >= 50:
            pool_size = 4
        else:
            pool_size = 1

        fastest_server = random.choice(fastest_pool[:pool_size])["Name"]

        return fastest_server

    def get_server_value(self, servername, key, servers):
        """Return the value of a key for a given server.

        Args:
            servername (string): servername [PT#1]
            key (string): keyword that contains servernames in json
            servers (list): a list containing the servers
        """
        value = [server[key] for server in servers if server['Name'] == servername]
        return value[0]

    def get_country_name(self, code):
        """Return the full name of a country from a specified code.

        Args:
            code (string): country code [PT|SE|CH]
        Returns:
            string:
                country name if found, else returns the code
        """
        from lib.country_codes import country_codes
        return country_codes.get(code, code)

    def is_servername_valid(self, servername):
        """Checks if the provided servername is in a valid format.

        Args:
            servername (string): the servername [SE-PT#1]
        Returns:
            bool
        """
        if not isinstance(servername, str):
            raise TypeError(
                "Incorrect object type, "
                + "str is expected but got {} instead".format(type(servername))
            )

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
