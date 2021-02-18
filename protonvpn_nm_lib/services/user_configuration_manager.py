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
        """Protocol get property."""
        user_configs = self.get_user_configurations()
        return user_configs[
            UserSettingEnum.CONNECTION.value
        ][UserSettingConnectionEnum.DEFAULT_PROTOCOL.value]

    @property
    def dns(self):
        """DNS get property."""
        user_configs = self.get_user_configurations()

        dns_status = user_configs[
            UserSettingEnum.CONNECTION.value
        ][UserSettingConnectionEnum.DNS.value][
            UserSettingConnectionEnum.DNS_STATUS.value
        ]

        custom_dns = user_configs[
            UserSettingEnum.CONNECTION.value
        ][UserSettingConnectionEnum.DNS.value][
            UserSettingConnectionEnum.CUSTOM_DNS.value
        ]

        return (dns_status, [custom_dns])

    @property
    def killswitch(self):
        """Killswitch get property."""
        user_configs = self.get_user_configurations()
        return user_configs[
            UserSettingEnum.CONNECTION.value
        ][UserSettingConnectionEnum.KILLSWITCH.value]

    @property
    def netshield(self):
        """Netshield get property."""
        user_configs = self.get_user_configurations()
        try:
            return user_configs[
                UserSettingEnum.CONNECTION.value
            ][UserSettingConnectionEnum.NETSHIELD.value]
        except KeyError:
            return 0

    def update_default_protocol(self, protocol):
        """Update default protocol.

        Args:
            protocol (ProtocolEnum): protocol type
        """
        if protocol not in [
            ProtocolEnum.TCP,
            ProtocolEnum.UDP,
            ProtocolEnum.IKEV2,
            ProtocolEnum.WIREGUARD,
        ]:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingEnum.CONNECTION.value][UserSettingConnectionEnum.DEFAULT_PROTOCOL.value] = protocol # noqa
        self.set_user_configurations(user_configs)

    def update_dns(self, status, custom_dns=None):
        """Update DNS setting.

        Args:
            status (UserSettingStatusEnum): DNS status
            custom_dns (list|None): Either list with IPs or None
        """
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()

        user_configs[UserSettingEnum.CONNECTION.value][
            UserSettingConnectionEnum.DNS.value
        ][UserSettingConnectionEnum.DNS_STATUS.value] = status # noqa
        user_configs[UserSettingEnum.CONNECTION.value][
            UserSettingConnectionEnum.DNS.value
        ][UserSettingConnectionEnum.CUSTOM_DNS.value] = custom_dns # noqa

        self.set_user_configurations(user_configs)

    def update_killswitch(self, status):
        """Update Kill Switch setting.

        Args:
            status (UserSettingStatusEnum): Kill Switch status
        """
        if status not in CONFIG_STATUSES:
            raise KeyError("Illegal options")

        user_configs = self.get_user_configurations()
        user_configs[UserSettingEnum.CONNECTION.value][
            UserSettingConnectionEnum.KILLSWITCH.value
        ] = status # noqa
        self.set_user_configurations(user_configs)

    def update_netshield(self, status):
        """Update NetShield setting.

        Args:
            status (int): matching value for NetShield
        """
        status_exists = False
        for k, v in NETSHIELD_STATUS_DICT.items():
            if k == status:
                status_exists = True
                break

        if not status_exists:
            raise KeyError("Illegal netshield option")

        user_configs = self.get_user_configurations()
        user_configs[
            UserSettingEnum.CONNECTION.value
        ][UserSettingConnectionEnum.NETSHIELD.value] = status
        self.set_user_configurations(user_configs)

    def reset_default_configs(self):
        """Reset user configurations to default values."""
        self.init_configuration_file(True)

    def init_configuration_file(self, force_init=False):
        """Initialize configurations file.

        Args:
            force_init (bool): if True then overwrites current configs
        """
        if not os.path.isfile(self.user_config_filepath) or force_init: # noqa
            self.set_user_configurations(USER_CONFIG_TEMPLATE)

    def get_user_configurations(self):
        """Get user configurations from file. Reads from file.

        Returns:
            dict(json)
        """
        with open(self.user_config_filepath, "r") as f:
            return json.load(f)

    def set_user_configurations(self, config_dict):
        """Set user configurations. Writes to file.

        Args:
            config_dict (dict): user configurations
        """
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
