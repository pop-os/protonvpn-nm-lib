from .. import exceptions
from ..constants import KILLSWITCH_STATUS_TEXT, SUPPORTED_PROTOCOLS
from ..enums import (DisplayUserSettingsEnum, KillswitchStatusEnum,
                     NetshieldTranslationEnum, ProtocolEnum,
                     ProtocolImplementationEnum, ServerTierEnum,
                     UserSettingConnectionEnum, UserSettingStatusEnum)
from ..logger import logger


class UserSettings:

    def _get_user_settings(self, raw_format=False):
        settings_dict = {
            DisplayUserSettingsEnum.PROTOCOL: self._get_protocol(),
            DisplayUserSettingsEnum.KILLSWITCH: self._get_killswitch(),
            DisplayUserSettingsEnum.DNS: self._get_dns(),
            DisplayUserSettingsEnum.CUSTOM_DNS: self._get_dns(True),
            DisplayUserSettingsEnum.NETSHIELD: self._get_netshield(),
        }

        if raw_format:
            return settings_dict

        return self.__transform_user_setting_to_readable_format(settings_dict)

    def __transform_user_setting_to_readable_format(self, raw_format):
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
        return self.user_conf_manager.netshield

    def _set_netshield(self, ns_option):
        # Public method providade by protonvpn_lib
        self._set_self_session()
        if not ns_option and self.user_manager.tier == ServerTierEnum.FREE:
            raise Exception(
                "\nBrowse the Internet free of malware, ads, "
                "and trackers with NetShield.\n"
                "To use NetShield, upgrade your subscription at: "
                "https://account.protonvpn.com/dashboard"
            )

        self.user_conf_manager.update_netshield(ns_option)

    def _get_killswitch(self):
        return self.user_conf_manager.killswitch

    def _set_killswitch(self, kill_switch_option):
        try:
            self.ks_manager.update_from_user_configuration_menu(
                kill_switch_option
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
            self.user_conf_manager.update_killswitch(kill_switch_option)

    def _get_protocol(self):
        return self.user_conf_manager.default_protocol

    def _set_protocol(self, protocol):
        """Set default protocol setting.

        Args:
            Namespace (object): list objects with cli args
        """
        logger.info("Setting protocol to: {}".format(protocol))

        try:
            protocol = ProtocolEnum(protocol)
        except (ValueError, TypeError):
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

    def _is_valid_ip(self, ip):
        return self.user_conf_manager.is_valid_ip(ip)

    def _get_dns(self, custom_dns=False):
        get_dns = UserSettingConnectionEnum.DNS_STATUS
        if custom_dns:
            get_dns = UserSettingConnectionEnum.CUSTOM_DNS

        user_configs = self.user_conf_manager.get_user_configurations()
        dns_settings = user_configs[UserSettingConnectionEnum.DNS][
            get_dns
        ]
        return dns_settings

    def _reset_to_default_configs(self, _=None):
        """Public method.

        Resets user configuration to default value.
        """
        # should it disconnect prior to resetting user configurations ?
        try:
            self.user_conf_manager.reset_default_configs()
        except (exceptions.ProtonVPNException, Exception) as e:
            raise Exception(e)
