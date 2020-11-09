import json
import os
import re

from ..constants import (
    CONFIG_STATUSES,
    PROTON_XDG_CONFIG_HOME,
    USER_CONFIG_TEMPLATE,
    USER_CONFIGURATIONS_FILEPATH
)
from ..enums import (
    ProtocolEnum,
    UserSettingEnum,
    UserSettingStatusEnum,
    UserSettingConnectionEnum
)


class UserConfigurationManager():
    def __init__(self):
        if not os.path.isdir(PROTON_XDG_CONFIG_HOME):
            os.makedirs(PROTON_XDG_CONFIG_HOME)
        self.init_configuration_file()

    @property
    def default_protocol(self):
        """Default protocol get property."""
        user_configs = self.get_user_configurations()
        return user_configs[
            UserSettingEnum.CONNECTION
        ][UserSettingConnectionEnum.DEFAULT_PROTOCOL]

    @property
    def dns(self):
        """DNS get property."""
        user_configs = self.get_user_configurations()

        dns_status = user_configs[
            UserSettingEnum.CONNECTION
        ][UserSettingConnectionEnum.DNS][UserSettingConnectionEnum.DNS_STATUS]

        custom_dns = user_configs[
            UserSettingEnum.CONNECTION
        ][UserSettingConnectionEnum.DNS][UserSettingConnectionEnum.CUSTOM_DNS]

        return (dns_status, [custom_dns])

    @property
    def killswitch(self):
        """Killswitch get property."""
        user_configs = self.get_user_configurations()
        return user_configs[
            UserSettingEnum.CONNECTION
        ][UserSettingConnectionEnum.KILLSWITCH]

    def update_default_protocol(self, protocol):
        if protocol not in [
            ProtocolEnum.TCP,
            ProtocolEnum.UDP,
            ProtocolEnum.IKEV2,
            ProtocolEnum.WIREGUARD,
        ]:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingEnum.CONNECTION][UserSettingConnectionEnum.DEFAULT_PROTOCOL] = protocol # noqa
        self.set_user_configurations(user_configs)

    def update_dns(self, status, custom_dns=None):
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()

        user_configs[UserSettingEnum.CONNECTION][UserSettingConnectionEnum.DNS][UserSettingConnectionEnum.DNS_STATUS] = status # noqa
        if status == UserSettingStatusEnum.CUSTOM:
            user_configs[UserSettingEnum.CONNECTION][UserSettingConnectionEnum.DNS][UserSettingConnectionEnum.CUSTOM_DNS] = custom_dns # noqa

        self.set_user_configurations(user_configs)

    def update_killswitch(self, status):
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingEnum.CONNECTION][UserSettingConnectionEnum.KILLSWITCH] = status # noqa
        self.set_user_configurations(user_configs)

    def update_split_tunneling(self, status, ip_list=None):
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

    def reset_default_configs(self):
        self.init_configuration_file(True)

    def init_configuration_file(self, force_init=False):
        if not os.path.isfile(USER_CONFIGURATIONS_FILEPATH) or force_init:
            self.set_user_configurations(USER_CONFIG_TEMPLATE)

    def get_user_configurations(self):
        with open(USER_CONFIGURATIONS_FILEPATH, "r") as f:
            return json.load(f)

    def set_user_configurations(self, config_dict):
        with open(USER_CONFIGURATIONS_FILEPATH, "w") as f:
            json.dump(config_dict, f, indent=4)

    def is_valid_ip(self, ipaddr):
        valid_ip_re = re.compile(
            r'^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.'
            r'(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)'
            r'(/(3[0-2]|[12][0-9]|[1-9]))?$'  # Matches CIDR
        )

        if valid_ip_re.match(ipaddr):
            return True

        return False
