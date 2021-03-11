import json
import random

from ... import exceptions
from ...constants import CACHED_SERVERLIST
from ...enums import FeatureEnum
from ...logger import logger
from .logical_server import LogicalServer


class ServerList:
    """Server List class.

    This class holds a list of LogicalServer objects.
    It also provides methods to seralize the serverlist.

    This class never modifies the local server list, unless
    self.reload_servers() is called. All other methods that
    appearently manipulate the server list, actually do
    so always by always returning a new list,
    thus leaving the server_list property untouched at all time.
    """
    _servers = []
    CACHED_SERVERLIST = CACHED_SERVERLIST

    @property
    def servers(self):
        return self._servers

    @staticmethod
    def instantiate_class():
        server_list = ServerList()
        return server_list

    @staticmethod
    def load_servers_from_dict(servers):
        server_list = ServerList()
        server_list.reload_servers(
            servers
        )

        return server_list

    @staticmethod
    def load_servers_from_file():
        """Instantiates class by loading servers directly
        from cache.

        Returns:
            list
        """
        server_list = ServerList()
        server_list.reload_servers(
            server_list.get_cached_serverlist()
        )

        return server_list

    def get_cached_serverlist(self):
        try:
            with open(self.CACHED_SERVERLIST, "r") as f:
                server_list = json.load(f)
            return server_list
        except FileNotFoundError as e:
            logger.exception(
                "[!] MissingCacheError: {}.".format(e)
            )
            raise exceptions.MissingCacheError(
                "Server cache not found. {}".format(e)
            )

    def serialize_servers_to_dict(self):
        writeable_dict_to_file = {"LogicalServers": []}

        for logical_server in self.servers:
            writeable_dict_to_file["LogicalServers"].append(
                logical_server.get_serialized_server()
            )

        return writeable_dict_to_file

    def reload_servers(self, server_list):
        """Reload server list instance.

        Args:
            server_list (dict): raw server list
                from file.
        """
        self._servers = []
        for server in server_list["LogicalServers"]:
            self._servers.append(LogicalServer(server))

    def get_matching_domain(self, logical_server, physical_server):
        """Get matching domaing for featureless or secure-core servers.

        Args:
            exit_IP (string): server exit IP
            server_feature (FeatureEnum): FeatureEnum object

        Returns:
            string: matching server domain
        """
        _list = [FeatureEnum.NORMAL, FeatureEnum.SECURE_CORE]
        features = FeatureEnum(logical_server.features)
        if features in _list:
            for server in self.servers:
                for _phys_server in server.servers:
                    if physical_server.exit_ip == _phys_server.entry_ip:
                        return _phys_server.domain

        return physical_server.domain

    def get_fastest_server(self, server_list):
        """Get fastest server.

        Args:
            server_list (list)

        Returns:
            tuple: same output as from get_random_server()
        """
        logger.info("Getting fastest server")
        fastest_pool = self.get_fastest_server_pool(server_list)
        return self.get_random_server(fastest_pool)

    def get_fastest_server_pool(self, server_list):
        """Get fastest server pool.

        Returns:
            pool list with fastest servers
        """
        # Sort servers by "speed" and select top n according to pool_size
        fastest_pool = self.get_sorted_servers_by_fastest(server_list)

        pool_size = 1
        if len(fastest_pool) >= 50:
            pool_size = 4

        return fastest_pool[:pool_size]

    def get_sorted_servers_by_fastest(self, server_list):
        """Sorts server list by best score.

        The lower the score, the better is the server ranked
        for connecting to.

        Returns:
            list
        """
        fastest_pool = sorted(
            server_list, key=lambda server: server.score
        )
        return fastest_pool

    def get_random_server(self, server_pool):
        """Get a random server from a server pool.

        Args:
            server_pool (list): pool with logical servers

        Returns:
            LogicalServer object
        """
        self.ensure_servers_is_list(server_pool)
        random_server = random.choice(server_pool)

        return random_server

    def get_random_physical_server(self, logical_server):
        """Get physical server at random.

        Args:
            physical_servers (list(dict)): list with physical servers

        Return:
            dict: with server information
        """
        logger.info("Selecting random physical server")
        enabled_servers = [
            server
            for server
            in logical_server.servers
            if server.status == 1
        ]
        if len(enabled_servers) == 0:
            logger.error("List of physical servers is empty")
            raise exceptions.EmptyServerListError("No servers could be found")

        random_server = random.choice(enabled_servers)
        logger.info("Saving server entry IP: \"{}\"".format(
            random_server.entry_ip
        ))
        random_server.domain = self.get_matching_domain(
            logical_server, random_server
        )

        return random_server

    def ensure_servers_is_list(self, server_list):
        """Ensures that the provided server list is a list object."""
        if not isinstance(server_list, list):
            err_msg = "Incorrect object type, "\
                "list is expected but got {} instead".format(
                    type(server_list)
                )
            logger.error(
                "[!] TypeError: {}. Raising exception.".format(err_msg)
            )
            raise TypeError(err_msg)
