import json
import os

from ..constants import (
    PROTON_XDG_CONFIG_HOME,
    USER_CONFIG_TEMPLATE,
    USER_CONFIGURATIONS_FILEPATH,
    CONFIG_STATUSES
)
from ..enums import (
    UserSettingsEnum,
    UserSettingsStatusEnum,
    ProtocolEnum
)


class UserConfigurationManager():
    def __init__(self):
        if not os.path.isdir(PROTON_XDG_CONFIG_HOME):
            os.makedirs(PROTON_XDG_CONFIG_HOME)
        self.init_configuration_file()

    def update_default_protocol(self, protocol):
        print("protocol: ",  protocol)
        if protocol not in [
            ProtocolEnum.TCP,
            ProtocolEnum.UDP,
            ProtocolEnum.IKEV2,
            ProtocolEnum.WIREGUARD,
        ]:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingsEnum.CONNECTION]["default_protocol"] = protocol # noqa
        self.set_user_configurations(user_configs)

    def update_dns(self, status, custom_dns=None):
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()

        user_configs[UserSettingsEnum.CONNECTION]["dns"]["status"] = status
        if status == UserSettingsStatusEnum.CUSTOM:
            user_configs[UserSettingsEnum.CONNECTION]["dns"]["custom_dns"] = custom_dns # noqa

        self.set_user_configurations(user_configs)

    def update_killswitch(self, status):
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingsEnum.CONNECTION]["killswitch"]

    def update_split_tunneling(self, status, ip_list=None):
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        print("manage split tunneling")

    def reset_default_configs(self):
        self.init_configuration_file(True)

    def init_configuration_file(self, force_init=False):
        if not os.path.isfile(USER_CONFIGURATIONS_FILEPATH) or not force_init:
            self.set_user_configurations(USER_CONFIG_TEMPLATE)

    def get_user_configurations(self):
        with open(USER_CONFIGURATIONS_FILEPATH, "r") as f:
            return json.load(f)

    def set_user_configurations(self, config_dict):
        with open(USER_CONFIGURATIONS_FILEPATH, "w") as f:
            json.dump(config_dict, f, indent=4)
