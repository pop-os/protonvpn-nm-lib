from ..enums import ServerInfoEnum, FeatureEnum, ConnectionMetadataEnum
from ..logger import logger
from ..constants import SUPPORTED_FEATURES
from .. import exceptions


class ProtonVPNServer:
    """Server Class.
    Use it to get information about a specific server.

    Exposes methods:
        _ensure_servername_is_valid(servername: String)
        _get_server_information(server_list: List, servername: String)

    Description:
    _ensure_servername_is_valid()
        Ensures that the provided is valid. This is done by matching the
        provided servername against a regex pattern.

    _get_server_information()
        Gets information about a server, based on the provided servername and
        server list. It returns itself.

    Public properties:
        SERVERNAME
        COUNTRY
        CITY
        LOAD
        TIER
        FEATURE_LIST
        ENTRY_COUNTRY
        REGION
        LATITUDE
        LONGITUDE
    """
    def __init__(self, server_manager, connection):
        self.__server_manager = server_manager
        self.__connection = connection
        self.SERVERNAME = None
        self.COUNTRY = None
        self.COUNTRY_CODE = None
        self.CITY = None
        self.LOAD = None
        self.TIER = None
        self.FEATURE_LIST = None
        self.ENTRY_COUNTRY = None
        self.ENTRY_COUNTRY_CODE = None
        self.REGION = None
        self.LATITUDE = None
        self.LONGITUDE = None

    def _ensure_servername_is_valid(self, servername):
        """Ensures if the provided servername is valid.

        Args:
            servername (string)
        """
        if (
            not self.__server_manager.is_servername_valid(servername)
        ):
            raise Exception(
                "IllegalServername: Invalid servername {}".format(
                    servername
                )
            )

    def _get_server_information(self, server_list, servername=None):
        """Get server information.

        Args:
            servername (string): optional
            if not specified, then the servername will be fetched
            from the current connection metadata file.

        Returns:
            Server
        """
        if not servername:
            conn_status = self.__connection._get_connection_metadata()
            try:
                servername = conn_status[ConnectionMetadataEnum.SERVER.value]
            except KeyError:
                servername = None

        return self.__extract_server_info(
            servername, server_list
        )

    def __extract_server_info(self, servername, server_list):
        """Extract server information.

        Args:
            servername (string): servername [PT#1]

        Returns:
            dict:
                Keys: ServerInfoEnum
        """
        try:
            country_code = self.__server_manager.extract_server_value(
                servername, ServerInfoEnum.COUNTRY.value, server_list
            )
            country = self.__server_manager.extract_country_name(country_code)

            load = self.__server_manager.extract_server_value(
                servername, ServerInfoEnum.LOAD.value, server_list
            )
            features = [
                self.__server_manager.extract_server_value(
                    servername, ServerInfoEnum.FEATURES.value, server_list
                )
            ]

            city = self.__server_manager.extract_server_value(
                servername, ServerInfoEnum.CITY.value, server_list
            )

            region = self.__server_manager.extract_server_value(
                servername, ServerInfoEnum.REGION.value, server_list
            )

            location = self.__server_manager.extract_server_value(
                servername, ServerInfoEnum.LOCATION.value, server_list
            )
            lat = location.get("Lat")
            long = location.get("Long")

            entry_country_code = self.__server_manager.extract_server_value(
                servername, ServerInfoEnum.ENTRY_COUNTRY.value, server_list
            )
            entry_country = self.__server_manager.extract_country_name(
                entry_country_code
            )

            tier = [
                self.__server_manager.extract_server_value(
                    servername, ServerInfoEnum.TIER.value, server_list
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

        self.SERVERNAME = servername
        self.COUNTRY = country
        self.COUNTRY_CODE = country_code
        self.CITY = city
        self.LOAD = load
        self.TIER = tier
        self.FEATURE_LIST = feature_list
        self.ENTRY_COUNTRY = entry_country
        self.ENTRY_COUNTRY_CODE = country_code
        self.REGION = region
        self.LATITUDE = lat
        self.LONGITUDE = long

        return self
