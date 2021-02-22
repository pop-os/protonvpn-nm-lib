class ProtonVPNCountry:
    """Country Class.
    Use it to get country name and check if country codes exist.

    Exposes method:
        _get_country_name(country_code: String)
        _check_country_exists(country_code: String)

    Description:
    _get_country_name()
        Gets a country name based on the provided country code in
        string (ISO) format.
    _check_country_exists()
        Checks if a given country code exists.
    """

    def __init__(self, __server_manager):
        self.__server_manager = __server_manager

    def _get_country_name(self, country_code):
        """Get country name of a given country code.

        Args:
            country_code (string): ISO format
        """
        return self.__server_manager.extract_country_name(country_code)

    def _check_country_exists(self, country_code):
        """Checks if given country code exists.

        Args:
            country_code (string): ISO format

        Returns:
            bool
        """
        return (
            True
            if self.__server_manager.extract_country_name(country_code)
            else False
        )
