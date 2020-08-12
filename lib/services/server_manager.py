import datetime
import re
import json
import random
import os
from lib.constants import CACHED_SERVERLIST, PROTON_XDG_CACHE_HOME
from lib import exceptions


class ServerManager():
    def __init__(self, cert_manager):
        self.cert_manager = cert_manager

    def fastest(self, session, protocol, *_):
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
        """Connect to the fastest server in a specific country."""
        country_code = args[0][1].strip().upper()
        self.pull_server_data(session)
        servers = self.get_servers(session)

        # ProtonVPN Features: 1: SECURE-CORE, 2: TOR, 4: P2P
        excluded_features = [1, 2]

        # Filter out excluded features and countries
        server_pool = []
        for server in servers:
            if server["Features"] not in excluded_features and server["ExitCountry"] == country_code:
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
        """Connect to a single given server directly"""
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
        """Connect to the fastest server in a specific country."""
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
        """Connect to a random ProtonVPN Server."""
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

    def pull_server_data(self, session, force=False):
        """Pull current server data from the ProtonVPN API."""
        refresh_interval = 45

        if not os.path.isdir(PROTON_XDG_CACHE_HOME):
            os.mkdir(PROTON_XDG_CACHE_HOME)

        try:
            last_modified_time = datetime.datetime.fromtimestamp(
                os.path.getmtime(CACHED_SERVERLIST)
            )
        except FileNotFoundError:
            last_modified_time = datetime.datetime.now()

        now_time = datetime.datetime.now()
        time_ago = now_time - datetime.timedelta(minutes=refresh_interval)

        # Cache servers only if they do not exists or
        # have been created > refresh_interval
        if (
            not os.path.isfile(CACHED_SERVERLIST)
        ) or (
            time_ago > last_modified_time
        ):

            data = session.api_request(endpoint="/vpn/logicals")

            with open(CACHED_SERVERLIST, "w") as f:
                json.dump(data, f)

    def get_ip_list(self, servername, servers):
        try:
            subservers = self.get_server_value(servername, "Servers", servers)
        except IndexError as e:
            raise IndexError(e)
        ip_list = [subserver["EntryIP"] for subserver in subservers]

        return ip_list

    def get_user_tier(self, session):
        data = session.api_request(endpoint="/vpn")
        return data["VPN"]["MaxTier"]

    def get_servers(self, session):
        """Return a list of all servers for the users Tier."""

        with open(CACHED_SERVERLIST, "r") as f:
            server_data = json.load(f)

        user_tier = self.get_user_tier(session)

        servers = server_data["LogicalServers"]

        # Sort server IDs by Tier
        return [server for server in servers if server["Tier"] <= user_tier and server["Status"] == 1] # noqa

    def get_fastest_server(self, server_pool):
        """Return the fastest server from a list of servers"""

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
        """Return the value of a key for a given server."""
        value = [server[key] for server in servers if server['Name'] == servername]
        return value[0]

    def get_country_name(self, code):
        """Return the full name of a country from code"""

        from lib.country_codes import country_codes
        return country_codes.get(code, code)

    def is_servername_valid(self, servername):
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

        return return_servername
