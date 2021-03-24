import datetime
import time

from ..constants import KILLSWITCH_STATUS_TEXT, SUPPORTED_PROTOCOLS
from ..enums import (ConnectionMetadataEnum, ConnectionStatusEnum,
                     KillSwitchInterfaceTrackerEnum, KillswitchStatusEnum,
                     NetshieldTranslationEnum, ProtocolEnum,
                     ProtocolImplementationEnum, MetadataEnum)
from ..logger import logger
from .environment import ExecutionEnvironment


class Status:
    """Status Class.
    Use it to get status information about the current
    ProtonVPN connection.
    """
    def __init__(self):
        self.user_settings = ExecutionEnvironment().settings
        self.server_list = ExecutionEnvironment().api_session.servers
        self.killswitch_obj = ExecutionEnvironment().killswitch
        self.connection_metadata = ExecutionEnvironment().connection_metadata

    def get_active_connection_status(self, readeable_format=True):
        """Get active connection status.

        Args:
            readeable_format (bool):
                If true then all content will be returnes in
                human readeable format, else all content is returned in
                enum objects.

        Returns:
            dict:
                Keys: ConnectionStatusEnum
        """
        connection_information = self.connection_metadata\
            .get_connection_metadata(
                MetadataEnum.CONNECTION
            )
        servername = connection_information[
            ConnectionMetadataEnum.SERVER.value
        ]
        protocol = connection_information[
            ConnectionMetadataEnum.PROTOCOL.value
        ]
        connected_time = connection_information[
            ConnectionMetadataEnum.CONNECTED_TIME.value
        ]

        try:
            exit_server_ip = connection_information[
                ConnectionMetadataEnum.DISPLAY_SERVER_IP.value
            ] # noqa
        except KeyError:
            exit_server_ip = "(Missing)"

        server = self.server_list.filter(
            lambda server: server.name.lower() == servername.lower()
        ).get_fastest_server()

        self.killswitch_obj.update_connection_status()

        ks_status = KillswitchStatusEnum.HARD
        if (
            not self.killswitch_obj.interface_state_tracker[self.killswitch_obj.ks_conn_name][ # noqa
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ] and self.user_settings.killswitch != KillswitchStatusEnum.DISABLED # noqa
        ):
            # if DISABLED then KS is currently not running,
            # otherwise it's ENABLED
            ks_status = KillswitchStatusEnum.DISABLED

        raw_dict = {
            ConnectionStatusEnum.SERVER_INFORMATION: server,
            ConnectionStatusEnum.PROTOCOL: ProtocolEnum(protocol),
            ConnectionStatusEnum.KILLSWITCH: ks_status,
            ConnectionStatusEnum.TIME: connected_time,
            ConnectionStatusEnum.NETSHIELD: self.user_settings.netshield, # noqa
            ConnectionStatusEnum.SERVER_IP: exit_server_ip,
        }
        if not readeable_format:
            return raw_dict

        return self.__transform_status_to_readable_format(raw_dict)

    def __transform_status_to_readable_format(self, raw_dict):
        """Transform raw dict to human redeable vales:

        Args:
            raw_dict (dict)

        Returns:
            dict
        """
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

        ks_user_setting = self.user_settings.killswitch

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

    def _convert_time_from_epoch(self, seconds_since_epoch):
        """Convert time from epoch to 24h.

        Args:
           time_in_epoch (string): time in seconds since epoch

        Returns:
            string: time in 24h format, since last connection was made
        """
        connection_time = (
            time.time()
            - int(seconds_since_epoch)
        )
        return str(
            datetime.timedelta(
                seconds=connection_time
            )
        ).split(".")[0]
