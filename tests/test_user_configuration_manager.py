import json
import os
import shutil

import pytest

from common import (PWD, KillswitchStatusEnum, ProtocolEnum,
                    UserConfigurationManager, UserSettingConnectionEnum,
                    UserSettingStatusEnum,
                    NetshieldTranslationEnum, NETSHIELD_STATUS_DICT)

test_user_config_dir = os.path.join(PWD, "test_config_protonvpn")
test_user_config_fp = os.path.join(
    test_user_config_dir, "test_user_configurations.json"
)


class TestSetUserConfigurationManager():
    ucm = UserConfigurationManager(
        test_user_config_dir,
        test_user_config_fp
    )

    def test_init_user_configurations_file(self):
        assert (os.path.isfile(test_user_config_fp))

    def test_set_correct_protocol(self):
        protocol = ProtocolEnum.TCP
        self.ucm.update_default_protocol(protocol)
        with open(test_user_config_fp) as f:
            json_configs = json.load(f)

            assert (
                json_configs[UserSettingConnectionEnum.DEFAULT_PROTOCOL.value]
                == protocol.value
            )

    @pytest.mark.parametrize(
        "protocol",
        ["", None, False, True, "tdp", 5]
    )
    def test_set_incorrect_protocol(self, protocol):
        with pytest.raises(KeyError):
            self.ucm.update_default_protocol(protocol)

    @pytest.mark.parametrize(
        "status,custom_dns_list",
        [
            (UserSettingStatusEnum.ENABLED, []),
            (UserSettingStatusEnum.CUSTOM, ["192.159.2.1"])
        ]
    )
    def test_set_correct_dns(self, status, custom_dns_list):
        self.ucm.update_dns(status, custom_dns_list)
        with open(test_user_config_fp) as f:
            json_configs = json.load(f)

        assert json_configs[
            UserSettingConnectionEnum.DNS.value
        ][UserSettingConnectionEnum.DNS_STATUS.value] == status.value

    @pytest.mark.parametrize(
        "status",
        [
            None, "SomeStatus", 9, ["hello"], {"no": "test"}
        ]
    )
    def test_set_incorrect_status_dns(self, status):
        with pytest.raises(KeyError):
            self.ucm.update_dns(status)

    @pytest.mark.parametrize(
        "ks_status",
        [
            KillswitchStatusEnum.DISABLED,
            KillswitchStatusEnum.SOFT,
            KillswitchStatusEnum.HARD,
        ]
    )
    def test_set_correct_killswitch(self, ks_status):
        self.ucm.update_killswitch(ks_status)
        with open(test_user_config_fp) as f:
            json_configs = json.load(f)

        assert (
            json_configs[UserSettingConnectionEnum.KILLSWITCH.value]
            == ks_status.value
        )

    @pytest.mark.parametrize(
        "ks_status",
        [
            "WrongStatus",
            "54",
            21,
            [],
            {}
        ]
    )
    def test_set_incorrect_killswitch(self, ks_status):
        with pytest.raises(KeyError):
            self.ucm.update_killswitch(ks_status)

    @pytest.mark.parametrize(
        "ns_status",
        [
            NetshieldTranslationEnum.DISABLED,
            NetshieldTranslationEnum.MALWARE,
            NetshieldTranslationEnum.ADS_MALWARE,
        ]
    )
    def test_set_correct_netshield(self, ns_status):
        self.ucm.update_netshield(ns_status)
        with open(test_user_config_fp) as f:
            json_configs = json.load(f)

        assert json_configs[UserSettingConnectionEnum.NETSHIELD.value] == ns_status.value

    @pytest.mark.parametrize(
        "ns_status",
        [
            "WrongStatus",
            "54",
            21,
            [],
            {}
        ]
    )
    def test_set_incorrect_netshield(self, ns_status):
        with pytest.raises(KeyError):
            self.ucm.update_netshield(ns_status)

    def test_reset_default_configs(self):
        self.ucm.reset_default_configs()
        with open(test_user_config_fp) as f:
            json_configs = json.load(f)

        assert json_configs[
            UserSettingConnectionEnum.KILLSWITCH.value
        ] == KillswitchStatusEnum.DISABLED.value

    def test_exists_get_user_configs(self):
        json_configs = self.ucm.get_user_configurations()
        assert json_configs[
            UserSettingConnectionEnum.KILLSWITCH
        ] == KillswitchStatusEnum.DISABLED

    def test_missing_get_user_configs(self):
        shutil.rmtree(test_user_config_dir)
        with pytest.raises(FileNotFoundError):
            self.ucm.get_user_configurations()

    @pytest.mark.parametrize(
        "ip",
        [
            "255.255.255.255",
            "192.168.0.1",
            "180.0.1.0",
        ]
    )
    def test_correct_is_valid_ip(self, ip):
        assert self.ucm.is_valid_ip(ip)

    @pytest.mark.parametrize(
        "ip",
        [
            {},
            180,
            [],
            True,
        ]
    )
    def test_incorrect_is_valid_ip(self, ip):
        with pytest.raises(ValueError):
            assert not self.ucm.is_valid_ip(ip)
