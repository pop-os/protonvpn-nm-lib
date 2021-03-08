from .server import Server
from .physical_server import PhysicalServer
from .location import Location
from ...enums import LogicalServerEnum, ServerEnum


class LogicalServer(Server):
    """Logical Server class.

    This class represent a logicals server which is
    provided  by the API.
    A get_serialized_server() is provided so that the
    contencts can be easily saved/stored to a file,
    as the object is transformed into a dict.
    """
    def __init__(self, logical_server):
        super().__init__(logical_server)

        self.name = logical_server.get(LogicalServerEnum.NAME.value)
        self.entry_country = logical_server.get(
            LogicalServerEnum.ENTRY_COUNTRY.value
        )
        self.exit_country = logical_server.get(
            LogicalServerEnum.EXIT_COUNTRY.value
        )
        self.tier = logical_server.get(LogicalServerEnum.TIER.value)
        self.features = logical_server.get(LogicalServerEnum.FEATURES.value)
        self.region = logical_server.get(LogicalServerEnum.REGION.value)
        self.city = logical_server.get(LogicalServerEnum.CITY.value)
        self.score = logical_server.get(LogicalServerEnum.SCORE.value)
        self.location = logical_server.get(LogicalServerEnum.LOCATION.value)
        self.servers = logical_server.get(LogicalServerEnum.SERVERS.value)
        self.load = logical_server.get(LogicalServerEnum.LOAD.value)

    def get_serialized_server(self):
        """Get serealized logical servers.

        This should be used only when saving to an external file,
        as python objects are not writeable/accesible to external sources.

        Returns:
            dict
        """
        return {
            LogicalServerEnum.NAME.value: self.name,
            LogicalServerEnum.ENTRY_COUNTRY.value: self.entry_country,
            LogicalServerEnum.EXIT_COUNTRY.value: self.exit_country,
            ServerEnum.DOMAIN.value: self.domain,
            LogicalServerEnum.TIER.value: self.tier,
            LogicalServerEnum.FEATURES.value: self.features,
            LogicalServerEnum.REGION.value: self.region,
            LogicalServerEnum.CITY.value: self.city,
            LogicalServerEnum.SCORE.value: self.score,
            ServerEnum.ID.value: self.server_id,
            LogicalServerEnum.LOCATION.value: self.location.get_serialized_location(), # noqa
            ServerEnum.STATUS.value: self.status,
            LogicalServerEnum.SERVERS.value: self.get_serialized_physicals_servers(), # noqa
            LogicalServerEnum.LOAD.value: self.load,
        }

    def get_serialized_physicals_servers(self):
        """Get serealized physical servers.

        Returns:
            dict
        """
        serialized_server = []
        for physical_server in self.servers:
            serialized_server.append(
                physical_server.get_serialized_server()
            )

        return serialized_server

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        try:
            self._name = new_name
        except AttributeError:
            pass

    @property
    def entry_country(self):
        return self._entry_country

    @entry_country.setter
    def entry_country(self, new_country):
        try:
            self._entry_country = new_country
        except AttributeError:
            pass

    @property
    def exit_country(self):
        return self._exit_country

    @exit_country.setter
    def exit_country(self, new_country):
        try:
            self._exit_country = new_country
        except AttributeError:
            pass

    @property
    def tier(self):
        return self._tier

    @tier.setter
    def tier(self, new_tier):
        try:
            self._tier = new_tier
        except AttributeError:
            pass

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, new_features):
        try:
            self._features = int(new_features)
        except (TypeError, AttributeError):
            pass

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, new_region):
        try:
            self._region = new_region
        except AttributeError:
            pass

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, new_city):
        try:
            self._city = new_city
        except AttributeError:
            pass

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, new_score):
        try:
            self._score = float(new_score)
        except (TypeError, AttributeError):
            pass

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, new_location):
        try:
            self._location = Location(new_location)
        except AttributeError:
            pass

    @property
    def servers(self):
        return self._servers

    @servers.setter
    def servers(self, physical_server_list):
        try:
            new_server_list = []
            for server in physical_server_list:
                instantiated_server = PhysicalServer(server)
                new_server_list.append(instantiated_server)
            self._servers = new_server_list
        except (TypeError, AttributeError):
            pass

    @property
    def load(self):
        return self._load

    @load.setter
    def load(self, new_load):
        try:
            self._load = float(new_load)
        except (TypeError, AttributeError):
            pass
