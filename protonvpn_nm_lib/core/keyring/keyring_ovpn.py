from ...enums import KeyringEnum


class KeyringOVPN:
    """KeyringOVPN class.

    This class is an abstraction of KeyringAdapter. It should be
    used only to manage ovpn credentials and user tier.
    """
    keyring_userdata = KeyringEnum.DEFAULT_KEYRING_USERDATA.value

    def __init__(self, keyring_adapter):
        self.keyring_adapter = keyring_adapter
        self._stored_ovpn_username = None
        self._stored_ovpn_password = None
        self._tier = None

    @property
    def ovpn_username(self):
        return self._stored_ovpn_username

    @property
    def ovpn_password(self):
        return self._stored_ovpn_password

    @property
    def tier(self):
        return self._tier

    @staticmethod
    def init(keyring_adapter):
        """Static method to initialize KeyringOVPN.

        Args:
            keyring_adapter (KeyringAdapter):
            can also be passed some other alternative
            implementation of a keyring.
        """
        user_data = KeyringOVPN(keyring_adapter)
        user_data.reload_properties()

        return user_data

    def store(self, user_data):
        """Store OVPN credentials.

        Due to the fact that tier is stored in the same
        entry as openvpn credentials, the tier has to be updated
        if openvpn credentials are updated.

        Instance properties are automatically updated once, so it is not
        needed to run self.reload_properties().

        Args:
            user_data (dict)
        """
        self._stored_ovpn_username = user_data["VPN"]["Name"]
        self._stored_ovpn_password = user_data["VPN"]["Password"]
        self._tier = self.__extract_tier(user_data)

        data = {
            "username": self._stored_ovpn_username,
            "password": self._stored_ovpn_password,
            "tier": self._tier
        }

        self.keyring_adapter.store_data(data, self.keyring_userdata)

    def __extract_tier(self, user_data):
        return user_data["VPN"]["MaxTier"]

    def reload_properties(self):
        """Reload class proprties.

        This methods gets the stored data and updates the properties
        if its instance.
        """
        stored_user_data = self.keyring_adapter.get_stored_data(
            self.keyring_userdata,
        )

        self._stored_ovpn_username = stored_user_data.get("username")
        self._stored_ovpn_password = stored_user_data.get("password")
        self._tier = stored_user_data.get("tier")

    def delete(self):
        """Delete ovpn entry.

        Session is deleted via the keyring adapater.
        """
        self.keyring_adapter.delete_stored_data(self.keyring_userdata)
        self._stored_ovpn_username = None
        self._stored_ovpn_password = None
        self._tier = None
