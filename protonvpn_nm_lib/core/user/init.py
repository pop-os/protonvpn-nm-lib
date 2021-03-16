from .settings_configurator import SettingsConfigurator
from .protonvpn_user import ProtonVPNUser
from .settings import Settings
from .killswitch import killswitch
from .session import session

settings_configurator = SettingsConfigurator()
settings = Settings(settings_configurator, killswitch)
protonvpn_user = ProtonVPNUser(session, settings)
settings.protonvpn_user = protonvpn_user
