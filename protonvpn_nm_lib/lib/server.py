from .. import exceptions
from ..constants import SUPPORTED_FEATURES
from ..enums import (ConnectionMetadataEnum, FeatureEnum, KillswitchStatusEnum,
                     ServerInfoEnum)
from ..logger import logger
from ..country_codes import country_codes


class ProtonVPNServer:

    def __init__(self, connection, session, server_manager, user_conf_manager):
        # library
        self.connection = connection
        self.session = session

        # services
        self.server_manager = server_manager
        self.user_conf_manager = user_conf_manager

    def _get_country_name(self, country_code):
        """Get country name of a given country code.

        Args:
            country_code (string): ISO format
        """
        return self.server_manager.extract_country_name(country_code)

    def _check_country_exists(self, country_code):
        """Checks if given country code exists.

        Args:
            country_code (string): ISO format

        Returns:
            bool
        """
        if country_code not in country_codes:
            return False

        return True

    def _get_filtered_servers(self, server_list):
        """Get filtered server list.

        Args:
            server_list (list(dict))

        Returns:
            list(dict)
        """
        try:
            return self.server_manager.filter_servers(
                server_list
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            return []

    def _get_server_list(self):
        """Get server list.

        Returns:
            list(dict)
        """
        try:
            return self.server_manager.extract_server_list()
        except (exceptions.ProtonVPNExceptionm, Exception) as e:
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
            country = self._get_country_name(server["ExitCountry"]) # noqa
            if country not in countries.keys():
                countries[country] = []
            countries[country].append(server["Name"])

        return countries

    def _get_server_information(self, servername=None):
        """Get server information.

        Args:
            servername (string): optional
            if not specified, then the servername will be fetched
            from the current connection metadata file.

        Returns:
            dict:
                Keys: ServerInfoEnum
        """
        if not servername:
            conn_status = self.connection._get_connection_metadata()
            try:
                servername = conn_status[ConnectionMetadataEnum.SERVER.value]
            except KeyError:
                servername = None

        return self.__extract_server_info(servername)

    def _refresh_servers(self):
        """Refresh cached server list."""
        session = self.session._get_session()
        if self.user_conf_manager.killswitch != KillswitchStatusEnum.HARD:
            try:
                session.cache_servers()
            except (exceptions.ProtonVPNException, Exception) as e:
                raise Exception(e)

    def _ensure_servername_is_valid(self, servername):
        """Ensures if the provided servername is valid.

        Args:
            servername (string)
        """
        if (
            not self.server_manager.is_servername_valid(servername)
        ):
            raise Exception(
                "IllegalServername: Invalid servername {}".format(
                    servername
                )
            )

    def __extract_server_info(self, servername):
        """Extract server information.

        Args:
            servername (string): servername [PT#1]

        Returns:
            dict:
                Keys: ServerInfoEnum
        """
        self._refresh_servers()
        self._ensure_servername_is_valid(servername)
        servers = self.server_manager.extract_server_list()
        try:
            country_code = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.COUNTRY.value, servers
            )
            country = self.server_manager.extract_country_name(country_code)

            load = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.LOAD.value, servers
            )
            features = [
                self.server_manager.extract_server_value(
                    servername, ServerInfoEnum.FEATURES.value, servers
                )
            ]

            city = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.CITY.value, servers
            )

            region = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.REGION.value, servers
            )

            location = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.LOCATION.value, servers
            )

            entry_country = self.server_manager.extract_server_value(
                servername, ServerInfoEnum.ENTRY_COUNTRY.value, servers
            )
            entry_country = self.server_manager.extract_country_name(
                entry_country
            )

            tier = [
                self.server_manager.extract_server_value(
                    servername, ServerInfoEnum.TIER.value, servers
                )
            ].pop()
        except IndexError as e:
            logger.exception("[!] IndexError: {}".format(e))
            raise IndexError(
                "\nThe server you have connected to is not available. "
                "If you are currently connected to the server, "
                "you will be soon disconnected. "
                "Please connect to another server."
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception("[!] Unknown error: {}".format(e))
            raise Exception("\nUnknown error: {}".format(e))

        feature_list = []
        for feature in features:
            feature = FeatureEnum(feature)
            if feature in SUPPORTED_FEATURES:
                feature_list.append(feature)

        return {
            ServerInfoEnum.SERVERNAME: servername,
            ServerInfoEnum.COUNTRY: country,
            ServerInfoEnum.CITY: city,
            ServerInfoEnum.LOAD: load,
            ServerInfoEnum.TIER: tier,
            ServerInfoEnum.FEATURES: feature_list,
            ServerInfoEnum.LOCATION: location,
            ServerInfoEnum.ENTRY_COUNTRY: entry_country,
            ServerInfoEnum.REGION: region,
        }
