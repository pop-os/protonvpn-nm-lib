import json
import os
import re

from ..constants import (
    CONFIG_STATUSES,
    PROTON_XDG_CONFIG_HOME,
    USER_CONFIG_TEMPLATE,
    USER_CONFIGURATIONS_FILEPATH,
    NETSHIELD_STATUS_DICT
)
from ..enums import (
    ProtocolEnum,
    UserSettingEnum,
    UserSettingConnectionEnum,
)


class UserConfigurationManager():
    def __init__(
        self,
        user_config_dir=PROTON_XDG_CONFIG_HOME,
        user_config_fp=USER_CONFIGURATIONS_FILEPATH
    ):
        self.user_config_filepath = user_config_fp
        if not os.path.isdir(user_config_dir):
            os.makedirs(user_config_dir)
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

    @property
    def netshield(self):
        """Killswitch get property."""
        user_configs = self.get_user_configurations()
        try:
            return user_configs[
                UserSettingEnum.CONNECTION
            ][UserSettingConnectionEnum.NETSHIELD]
        except KeyError:
            return 0

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

    def update_netshield(self, status):
        status_exists = False
        for k, v in NETSHIELD_STATUS_DICT.items():
            if k == status:
                status_exists = True
                break

        if not status_exists:
            raise KeyError("Illegal netshield option")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingEnum.CONNECTION][UserSettingConnectionEnum.NETSHIELD] = status # noqa
        self.set_user_configurations(user_configs)

    def reset_default_configs(self):
        self.init_configuration_file(True)

    def init_configuration_file(self, force_init=False):
        if not os.path.isfile(self.user_config_filepath) or force_init: # noqa
            self.set_user_configurations(USER_CONFIG_TEMPLATE)

    def get_user_configurations(self):
        with open(self.user_config_filepath, "r") as f:
            return json.load(f)

    def set_user_configurations(self, config_dict):
        with open(self.user_config_filepath, "w") as f:
            json.dump(config_dict, f, indent=4)

    def is_valid_ip(self, ipaddr):
        if not isinstance(ipaddr, str):
            raise ValueError("Invalid object type")

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
