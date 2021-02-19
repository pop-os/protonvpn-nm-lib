from ..constants import SUPPORTED_PROTOCOLS, KILLSWITCH_STATUS_TEXT
from ..enums import (ConnectionMetadataEnum, ConnectionStatusEnum,
                     KillswitchStatusEnum, ProtocolEnum,
                     ProtocolImplementationEnum, NetshieldTranslationEnum,
                     KillSwitchInterfaceTrackerEnum)
from ..logger import logger


class Status:

    def _get_connection_status(self, raw_format=False):

        connection_information = self._get_connection_metadata() # noqa
        servername = connection_information[ConnectionMetadataEnum.SERVER.value] # noqa
        protocol = connection_information[ConnectionMetadataEnum.PROTOCOL.value] # noqa
        connected_time = connection_information[ConnectionMetadataEnum.CONNECTED_TIME.value] # noqa
        try:
            exit_server_ip = connection_information[ConnectionMetadataEnum.DISPLAY_SERVER_IP.value] # noqa
        except KeyError:
            exit_server_ip = "(Missing)"

        # Public method providade by protonvpn_lib
        server_information_dict = self._get_server_information(servername)

        self.ks_manager.update_connection_status()

        ks_status = KillswitchStatusEnum.HARD
        if (
            not self.ks_manager.interface_state_tracker[self.ks_manager.ks_conn_name][ # noqa
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ] and self.user_conf_manager.killswitch != KillswitchStatusEnum.DISABLED # noqa
        ):
            # if DISABLED then KS is currently not running,
            # otherwise it's ENABLED
            ks_status = KillswitchStatusEnum.DISABLED

        raw_dict = {
            ConnectionStatusEnum.SERVER_INFORMATION: server_information_dict,
            ConnectionStatusEnum.PROTOCOL: ProtocolEnum(protocol),
            ConnectionStatusEnum.KILLSWITCH: ks_status,
            ConnectionStatusEnum.TIME: connected_time,
            ConnectionStatusEnum.NETSHIELD: self._get_netshield(),
            ConnectionStatusEnum.SERVER_IP: exit_server_ip,
        }
        if raw_format:
            return raw_dict

        return self.__transform_status_to_readable_format(raw_dict)

    def __transform_status_to_readable_format(self, raw_dict):
        server_information_dict = raw_dict[
            ConnectionStatusEnum.SERVER_INFORMATION
        ]
        raw_protocol = raw_dict[ConnectionStatusEnum.PROTOCOL]
        raw_ks = raw_dict[ConnectionStatusEnum.KILLSWITCH]
        raw_ns = raw_dict[ConnectionStatusEnum.NETSHIELD]
        raw_time = raw_dict[ConnectionStatusEnum.TIME]
        server_ip = raw_dict[ConnectionStatusEnum.SERVER_IP]

        # protocol
        if raw_protocol in SUPPORTED_PROTOCOLS[ProtocolImplementationEnum.OPENVPN]: # noqa
            transformed_protocol = "OpenVPN ({})".format(
                raw_protocol.value.upper()
            )
        else:
            transformed_protocol = raw_protocol.value.upper()

        # Public method providade by user_settings
        ks_user_setting = self._get_killswitch()

        # killswitch
        ks_add_text = ""

        logger.info("KS status: {} - User setting: {}".format(
            raw_ks, ks_user_setting
        ))

        if (
            raw_ks == KillswitchStatusEnum.DISABLED
            and ks_user_setting != KillswitchStatusEnum.DISABLED
        ):
            ks_add_text = "(Inactive, restart connection to activate KS)"

        transformed_ks = KILLSWITCH_STATUS_TEXT[ks_user_setting] + " " + ks_add_text # noqa

        # netshield
        netshield_status = {
            NetshieldTranslationEnum.MALWARE: "Malware", # noqa
            NetshieldTranslationEnum.ADS_MALWARE: "Ads and malware", # noqa
            NetshieldTranslationEnum.DISABLED: "Disabled" # noqa
        }
        transformed_ns = netshield_status[raw_ns]

        transformed_time = self._convert_time_from_epoch(
            raw_time
        )

        return {
            ConnectionStatusEnum.SERVER_INFORMATION: server_information_dict, # noqa
            ConnectionStatusEnum.PROTOCOL: transformed_protocol,
            ConnectionStatusEnum.KILLSWITCH: transformed_ks,
            ConnectionStatusEnum.TIME: transformed_time,
            ConnectionStatusEnum.NETSHIELD: transformed_ns,
            ConnectionStatusEnum.SERVER_IP: server_ip,
        }
