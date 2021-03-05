from .. import exceptions
from ..logger import logger
from ..enums import KillswitchStatusEnum


class ProtonVPNServerList:
    """ServerList Class.
    Use it to fetch a list with servers,
    list with filtered servers and refresh servers.

    Exposes method:
        _get_filtered_server_list(server_list: List)
        _get_server_list()
        _get_dict_with_country_servername(server_list: List)
        _refresh_servers()

    Description:
    _get_filtered_server_list()
        Get a list of filtered servers. By default, it filters servers
        based on user tier and server status.
    _get_server_list()
        Similar to _get_filtered_server_list() but instead it just gets
        all servers without applying any filtering.
    _get_dict_with_country_servername()
        Gets a dict where each country code in ISO format has a list of servers
        as their value.
    _refresh_servers()
        Caches the servers.
    """
    def __init__(
        self, connection, session, server, country,
        server_manager, user_conf_manager
    ):
        # library
        self.connection = connection
        self.session = session
        self.server = server
        self.country = country

        # core
        self.__server_manager = server_manager
        self.__user_conf_manager = user_conf_manager

    def _get_filtered_server_list(
        self,
        server_list, exclude_features,
        include_features, country_code,
        ignore_tier, ignore_server_status
    ):
        """Get filtered server list.

        Args:
            server_list (list(dict))
            exclude_features (list): [FeatureEnum.TOR, ...] (optional)
            include_features (list): [FeatureEnum.TOR, ...] (optional)
                exclude_features and include_features are mutually exclusive.
            country_code (string): country code PT|SE|CH (optional)
                returns servers belonging to specifiec country list.
            ignore_tier (bool): if user tier should be ignored. Filtering
                will not take into consideration the user tier. (optional)
            ignore_server_status (bool): if logical server status is to be
                ignored. If it is ignored, then servers that are unavaliable
                will be returned. (optional)

        Returns:
            list(dict)
        """
        try:
            return self.__server_manager.filter_servers(
                server_list, exclude_features=exclude_features,
                include_features=include_features,
                country_code=country_code,
                ignore_tier=ignore_tier,
                ignore_server_status=ignore_server_status
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            return []

    def _get_server_list(self):
        """Get server list.

        Returns:
            list(dict)
        """
        self._refresh_servers()
        try:
            return self.__server_manager.extract_server_list()
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            return []

    def _get_dict_with_country_servername(self, server_list):
        """Generate dict with {country:[servername]}.

        Args:
            server_list (list)
        Returns:
            dict: country_code: [servername]
                ie {PT: [PT#5, PT#8]}
        """
        countries = {}
        for server in server_list:
            servername = server["Name"]
            server = self.server._get_server_information(
                server_list, servername
            )
            country = self.country._get_country_name(server.COUNTRY)
            if country not in countries.keys():
                countries[country] = []
            countries[country].append(servername)

        return countries

    def _refresh_servers(self):
        """Refresh cached server list."""
        session = self.session._get_session()
        if self.__user_conf_manager.killswitch != KillswitchStatusEnum.HARD:
            try:
                session.cache_servers()
            except (exceptions.ProtonVPNException, Exception) as e:
                raise Exception(e)
