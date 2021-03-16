from ... import exceptions
from ...enums import ConnectionTypeEnum, FeatureEnum
from ...logger import logger
from ..servers import ServerFilter


class ServerConfigurator:
    """This class selects the server for appropriate connection type."""

    def __init__(self):
        self.user = None
        self.server_list = None
        self.server_filter = None

    @staticmethod
    def init(user, server_list, server_filter=ServerFilter()):
        server_configurator = ServerConfigurator()
        server_configurator.user = user
        server_configurator.server_list = server_list
        server_configurator.server_filter = server_filter

        return server_configurator

    def get_config_for_fastest_server(self):
        """Get configuration for fastest server.

        Returns:
            tuple
        """
        logger.info("Generating config for fastest server")
        self.server_list.reload_servers(
            self.server_list.get_cached_serverlist()
        )
        servers_list = self.server_list.servers
        default_filtered_servers = \
            self.server_filter.get_default_filtered_servers(
                servers_list,
                self.get_user_tier()
            )
        excluded_features = [
            FeatureEnum.SECURE_CORE,
            FeatureEnum.TOR,
            FeatureEnum.P2P
        ]
        filtered_servers = self.server_filter.get_servers_by_exclude_features( # noqa
            default_filtered_servers, excluded_features
        )

        if len(filtered_servers) == 0:
            err_msg = "No available servers could be found."
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        return self.server_list.get_fastest_server(filtered_servers)

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
        self.server_list.reload_servers(
            self.server_list.get_cached_serverlist()
        )
        servers_list = self.server_list.servers
        default_filtered_servers = \
            self.server_filter.get_default_filtered_servers(
                servers_list,
                self.get_user_tier()
            )
        country_servers = self.server_filter.get_servers_by_country_code(
            default_filtered_servers, country_code
        )

        excluded_features = [
            FeatureEnum.TOR, FeatureEnum.SECURE_CORE
        ]
        filtered_servers = self.server_filter.get_servers_by_exclude_features( # noqa
            country_servers,
            excluded_features,
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

        return self.server_list.get_fastest_server(filtered_servers)

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

        self.server_list.reload_servers(
            self.server_list.get_cached_serverlist()
        )
        servers_list = self.server_list.servers
        default_filtered_servers = \
            self.server_filter.get_default_filtered_servers(
                servers_list,
                self.get_user_tier()
            )
        filtered_servers = self.server_filter.get_server_by_name(
            default_filtered_servers,
            servername
        )

        if not filtered_servers:
            err_msg = "No available servers could be found for \"{}\"".format(
                servername
            )
            logger.error(
                "[!] EmptyServerListError: {}. Raising exception.".format(
                    err_msg
                )
            )
            raise exceptions.EmptyServerListError(err_msg)

        return self.server_list.get_random_server([filtered_servers])

    def get_config_for_fastest_server_with_specific_feature(
        self, feature
    ):
        """Get configuration to fastest server based on specified feature.

        Args:
            feature (ConnectionTypeEnum)

        Returns:
            tuple
        """
        self.server_list.reload_servers(
            self.server_list.get_cached_serverlist()
        )
        servers_list = self.server_list.servers
        default_filtered_servers = \
            self.server_filter.get_default_filtered_servers(
                servers_list,
                self.get_user_tier()
            )

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

        filtered_servers = self.server_filter.get_servers_by_include_features( # noqa
            default_filtered_servers,
            [feature]
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

        return self.server_list.get_fastest_server(filtered_servers)

    def get_config_for_random_server(self):
        """Get configuration to random server.

        Returns:
            tuple
        """
        self.server_list.reload_servers(
            self.server_list.get_cached_serverlist()
        )
        servers_list = self.server_list.servers
        default_filtered_servers = \
            self.server_filter.get_default_filtered_servers(
                servers_list,
                self.get_user_tier()
            )

        return self.server_list.get_random_server(default_filtered_servers)

    def get_user_tier(self):
        """Fetch user tier.

        Returns:
            int: current user session tier
        """
        self.user.session.keyring_ovpn.reload_properties()
        user_tier = self.user.tier
        if user_tier is None:
            raise TypeError(
                "User instance has to be set prior to getting its attribute"
            )

        return user_tier
