from .settings import Settings
from ..killswitch import KillSwitch


class ProtonVPNUser:
    """ProtonVPNUser class.

    A ProtonVPN user consists of two components:
     - Session
     - Settings
    By default it uses the Settings component, but something else
    can be provided, given that it implements same methods and
    properties.
    """
    def __init__(self, settings=Settings(), killswitch=KillSwitch()):
        self._session = None
        self.settings = settings
        self.settings.killswitch_obj = killswitch

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, new_session):
        self._session = new_session

    @property
    def ovpn_username(self):
        return self._session.keyring_ovpn.ovpn_username

    @property
    def ovpn_password(self):
        return self._session.keyring_ovpn.ovpn_password

    @property
    def tier(self):
        return self._session.keyring_ovpn.tier

    @property
    def protonvpn_username(self):
        """ProtonVPN username property."""
        return self._session.keyring_proton.protonvpn_username
