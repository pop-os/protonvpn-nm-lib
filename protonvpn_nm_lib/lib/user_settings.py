from .. import exceptions
from ..constants import (KILLSWITCH_STATUS_TEXT,
                         SUPPORTED_PROTOCOLS)
from ..enums import (DisplayUserSettingsEnum, NetshieldTranslationEnum,
                     ProtocolEnum, ProtocolImplementationEnum, ServerTierEnum,
                     UserSettingConnectionEnum, UserSettingStatusEnum,
                     UserTierEnum)
from ..logger import logger


class ProtonVPNUserSetting:

    def __init__(self, user_conf_manager, user_manager, ks_manager):
        self.user_conf_manager = user_conf_manager
        self.user_manager = user_manager
        self.ks_manager = ks_manager

    def _get_user_settings(self, readeable_format):
        """Get user settings.

        Args:
            readeable_format (bool):
                If true then all content will be returnes in
                human readeable format, else all content is returned in
                enum objects.

        Returns:
            dict:
                Keys: DisplayUserSettingsEnum
        """
        settings_dict = {
            DisplayUserSettingsEnum.PROTOCOL: self._get_protocol(),
            DisplayUserSettingsEnum.KILLSWITCH: self._get_killswitch(),
            DisplayUserSettingsEnum.DNS: self._get_dns(),
            DisplayUserSettingsEnum.CUSTOM_DNS: self._get_dns(True),
            DisplayUserSettingsEnum.NETSHIELD: self._get_netshield(),
        }

        if not readeable_format:
            return settings_dict

        return self.__transform_user_setting_to_readable_format(settings_dict)

    def __transform_user_setting_to_readable_format(self, raw_format):
        """Transform the dict in raw_format to human readeable format.

        Args:
            raw_format (dict)

        Returns:
            dict
        """
        raw_protocol = raw_format[DisplayUserSettingsEnum.PROTOCOL]
        raw_ks = raw_format[DisplayUserSettingsEnum.KILLSWITCH]
        raw_dns = raw_format[DisplayUserSettingsEnum.DNS]
        raw_custom_dns = raw_format[DisplayUserSettingsEnum.CUSTOM_DNS]
        raw_ns = raw_format[DisplayUserSettingsEnum.NETSHIELD]

        # protocol
        if raw_protocol in SUPPORTED_PROTOCOLS[ProtocolImplementationEnum.OPENVPN]: # noqa
            transformed_protocol = "OpenVPN ({})".format(
                raw_protocol.value.upper()
            )
        else:
            transformed_protocol = raw_protocol.value.upper()

        # killswitch
        transformed_ks = KILLSWITCH_STATUS_TEXT[raw_ks]

        # dns
        dns_status = {
            UserSettingStatusEnum.ENABLED: "Automatic",
            UserSettingStatusEnum.CUSTOM: "Custom: {}".format(
                ", ".join(raw_custom_dns)
            ),
        }
        transformed_dns = dns_status[raw_dns]

        # netshield
        netshield_status = {
            NetshieldTranslationEnum.MALWARE: "Malware", # noqa
            NetshieldTranslationEnum.ADS_MALWARE: "Ads and malware", # noqa
            NetshieldTranslationEnum.DISABLED: "Disabled" # noqa
        }
        transformed_ns = netshield_status[raw_ns]

        return {
            DisplayUserSettingsEnum.PROTOCOL: transformed_protocol,
            DisplayUserSettingsEnum.KILLSWITCH: transformed_ks,
            DisplayUserSettingsEnum.DNS: transformed_dns,
            DisplayUserSettingsEnum.NETSHIELD: transformed_ns,
        }

    def _get_netshield(self):
        """Get user netshield setting.

        Returns:
            NetshieldTranslationEnum
        """
        return self.user_conf_manager.netshield

    def _set_netshield(self, netshield_enum):
        """Set netshield to specified option.

        Args:
            netshield_enum (NetshieldTranslationEnum)
        """
        if (
            not netshield_enum
            and self.user_manager.tier == ServerTierEnum.FREE
        ):
            raise Exception(
                "\nBrowse the Internet free of malware, ads, "
                "and trackers with NetShield.\n"
                "To use NetShield, upgrade your subscription at: "
                "https://account.protonvpn.com/dashboard"
            )

        self.user_conf_manager.update_netshield(netshield_enum)

    def _get_killswitch(self):
        """Get user Kill Switch setting.

        Returns:
            KillswitchStatusEnum
        """
        return self.user_conf_manager.killswitch

    def _set_killswitch(self, killswitch_option):
        """Set Kill Switch to specified option.

        Args:
            killswitch_option (KillswitchStatusEnum)
        """
        try:
            self.ks_manager.update_from_user_configuration_menu(
                killswitch_option
            )
        except exceptions.DisableConnectivityCheckError as e:
            logger.exception(e)
            raise Exception(
                "\nUnable to set kill switch setting: "
                "Connectivity check could not be disabled.\n"
                "Please disable connectivity check manually to be able to use "
                "the killswitch feature."
            )
        except (exceptions.ProtonVPNException, Exception) as e:
            logger.exception(e)
            raise Exception(e)
        else:
            self.user_conf_manager.update_killswitch(killswitch_option)

    def _get_protocol(self):
        """Get user set default protocol.

        Returns:
            ProtocolEnum
        """
        return self.user_conf_manager.default_protocol

    def _set_protocol(self, protocol):
        """Set default protocol setting.

        Args:
            protocol (ProtocolEnum)
        """
        logger.info("Setting protocol to: {}".format(protocol))

        if not isinstance(protocol, ProtocolEnum):
            logger.error("Select protocol is incorrect.")
            raise Exception(
                "\nSelected option \"{}\" is either incorrect ".format(
                    protocol
                ) + "or protocol is (yet) not supported"
            )

        self.user_conf_manager.update_default_protocol(
            protocol
        )

        logger.info("Default protocol has been updated to \"{}\"".format(
            protocol
        ))

    def _set_dns(self, setting_status, custom_dns_ips=[]):
        """Set DNS setting.

        Args:
            Namespace (object): list objects with cli args
        """
        if not isinstance(setting_status, UserSettingStatusEnum):
            raise Exception("Invalid setting status \"{}\"".format(
                setting_status
            ))

        if custom_dns_ips:
            for dns_server_ip in custom_dns_ips:
                if not self._is_valid_ip(dns_server_ip):
                    logger.error("{} is an invalid IP".format(dns_server_ip))
                    raise Exception(
                        "\n{0} is invalid. "
                        "Please provide a valid IP DNS server.".format(
                            dns_server_ip
                        )
                    )

        try:
            self.user_conf_manager.update_dns(setting_status, custom_dns_ips)
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _get_dns(self, custom_dns=False):
        """Get user DNS setting.

        Args:
            custom_dns (bool):
            (optional) should be set to True
            if it is desired to get custom DNS values
            in a list.

        Returns:
            UserSettingStatusEnum | list
        """
        get_dns = UserSettingConnectionEnum.DNS_STATUS
        if custom_dns:
            get_dns = UserSettingConnectionEnum.CUSTOM_DNS

        user_configs = self.user_conf_manager.get_user_configurations()
        dns_settings = user_configs[UserSettingConnectionEnum.DNS][
            get_dns
        ]
        return dns_settings

    def _get_user_tier(self):
        """Get stored user tier.

        Returns:
            UserTierEnum
        """
        try:
            return UserTierEnum(self.user_manager.tier)
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)

    def _is_valid_ip(self, ip):
        """Check if provided IP is valid.

        Returns:
            bool
        """
        return self.user_conf_manager.is_valid_ip(ip)

    def _reset_to_default_configs(self):
        """Reset user configuration to default values."""
        # should it disconnect prior to resetting user configurations ?
        try:
            self.user_conf_manager.reset_default_configs()
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)
