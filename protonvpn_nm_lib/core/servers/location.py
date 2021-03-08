from ...enums import ServerLocation


class Location:
    """Location class.

    This class represents the location values of each logical server.
    Provides a method which returns a serealized location server.
    """
    def __init__(self, server_location):
        self.latitude = server_location.get(ServerLocation.LATITUDE.value)
        self.longitude = server_location.get(ServerLocation.LONGITUDE.value)

    def get_serialized_location(self):
        """Get serealized server location.

        This should be used only when saving to an external file,
        as python objects are not writeable/accesible to external sources.

        Returns:
            dict
        """
        return {
            ServerLocation.LATITUDE.value: self.latitude,
            ServerLocation.LONGITUDE.value: self.longitude,
        }

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, new_longitude):
        self._longitude = new_longitude

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, new_latitude):
        self._latitude = new_latitude
