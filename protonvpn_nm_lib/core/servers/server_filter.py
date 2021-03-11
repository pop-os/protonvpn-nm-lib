from ...logger import logger
from ...enums import FeatureEnum


class ServerFilter:
    def get_default_filtered_servers(self, servers, user_tier):
        """Get default filtered servers.

        This methos should be used when the desired ouput
        of server list is to have them filtered, so that all
        logical servers are enabled and servers tier equal or
        higher to a users tier.
        """
        active_servers = self.get_servers_by_server_status(
            servers, 1
        )
        default_filtered_servers = self.get_servers_by_tier(
            active_servers, user_tier
        )
        return default_filtered_servers

    def get_server_by_name(self, servers, servername):
        """Get server by servername.

        Args:
            servers (list(LogicalServer))
            servername (string):
                PT#12 or CH#13

        Returns:
            list with LogicalServer
        """
        logger.info("Filtering servers by servername")
        for logical_server in servers:
            if logical_server.name.lower() == servername.lower():
                return logical_server

        return {}

    def get_servers_by_server_status(self, servers, status):
        """Get servers by server status.

        Args:
            servers (list(LogicalServer))
            status (int): server status

        Returns:
            list with LogicalServer
        """
        logger.info("Filtering servers by status")
        servers_by_status = []
        for logical_server in servers:
            if logical_server.status == int(status):
                servers_by_status.append(logical_server)

        return servers_by_status

    def get_servers_by_country_code(self, servers, country_code):
        """Get servers by country code.

        Args:
            servers (list(LogicalServer))
            country_code (string): country code PT|SE|CH (optional)
                returns servers belonging to specifiec country list.
                country_code and servername are mutually exclusive.

        Returns:
            list with LogicalServer
        """
        logger.info("Filtering servers by country code")
        servers_by_country_code = []
        for logical_server in servers:
            if logical_server.exit_country.lower() == country_code.lower():
                servers_by_country_code.append(logical_server)

        return servers_by_country_code

    def get_servers_by_tier(self, servers, tier, enforce_same_tier=False):
        """Get servers by tier.

        Args:
            servers (list(LogicalServer))
            tier (int): user server/tier
            enforce_same_tier (bool): if true the servers will
                be selected only with matching tier.

        Returns:
            list with LogicalServer
        """
        logger.info("Filtering servers by tier")
        filtered_servers = []

        for logical_server in servers:
            if not enforce_same_tier and logical_server.tier <= int(tier):
                filtered_servers.append(logical_server)
            elif enforce_same_tier and logical_server.tier == int(tier):
                filtered_servers.append(logical_server)
            else:
                continue

        return filtered_servers

    def get_servers_by_include_features(self, servers, include_features):
        """Get servers by including specified features.

        Args:
            servers (list(LogicalServer))
            include_features (list): [FeatureEnum.TOR, ...]

        Returns:
            list with LogicalServer
        """
        logger.info("Filtering servers by include")

        filtered_servers = []

        for server in servers:
            server_feature = FeatureEnum(server.features or 0)
            if server_feature in include_features:
                filtered_servers.append(server)

        return filtered_servers

    def get_servers_by_exclude_features(self, servers, exclude_features):
        """Get servers by excluding specified features.

        Args:
            servers (list(LogicalServer))
            exclude_features (list): [FeatureEnum.TOR, ...]

        Returns:
            list with LogicalServer
        """
        logger.info("Filtering servers by exclude")

        filtered_servers = []
        for server in servers:
            server_feature = FeatureEnum(server.features or 0)
            if server_feature not in exclude_features:
                filtered_servers.append(server)

        return filtered_servers
