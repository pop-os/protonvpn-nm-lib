import datetime
import time

from ..constants import KILLSWITCH_STATUS_TEXT, SUPPORTED_PROTOCOLS
from ..enums import (ConnectionMetadataEnum, ConnectionStatusEnum,
                     KillSwitchInterfaceTrackerEnum, KillswitchStatusEnum,
                     NetshieldTranslationEnum, ProtocolEnum,
                     ProtocolImplementationEnum)
from ..logger import logger


class ProtonVPNStatus:
    """Status Class.
    Use it to get status information about the current
    ProtonVPN connection.

    Exposes methods:
        _get_active_connection_status()
        _convert_time_from_epoch(seconds_since_epoch: String)

    Description:
    _get_active_connection_status()
        Returns a dict with ConnectionStatusEnum keys.

    _convert_time_from_epoch()
        Converts the provided time in seconds since epoch to
        human readeable time (24h).
    """
    def __init__(
        self, connection, server, server_list,
        ks_manager, user_settings, user_conf_manager
    ):
        # library
        self.connection = connection
        self.server = server
        self.server_list = server_list
        self.user_settings = user_settings

        # core
        self.__ks_manager = ks_manager
        self.__user_conf_manager = user_conf_manager

    def _get_active_connection_status(self, readeable_format):
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
        connection_information = self.connection._get_connection_metadata() # noqa
        servername = connection_information[ConnectionMetadataEnum.SERVER.value] # noqa
        protocol = connection_information[ConnectionMetadataEnum.PROTOCOL.value] # noqa
        connected_time = connection_information[ConnectionMetadataEnum.CONNECTED_TIME.value] # noqa
        try:
            exit_server_ip = connection_information[ConnectionMetadataEnum.DISPLAY_SERVER_IP.value] # noqa
        except KeyError:
            exit_server_ip = "(Missing)"

        self.server._ensure_servername_is_valid(servername)
        server_information_dict = self.server._get_server_information(
            server_list=self.server_list._get_server_list(),
            servername=servername
        )

        self.__ks_manager.update_connection_status()

        ks_status = KillswitchStatusEnum.HARD
        if (
            not self.__ks_manager.interface_state_tracker[self.__ks_manager.ks_conn_name][ # noqa
                KillSwitchInterfaceTrackerEnum.IS_RUNNING
            ] and self.__user_conf_manager.killswitch != KillswitchStatusEnum.DISABLED # noqa
        ):
            # if DISABLED then KS is currently not running,
            # otherwise it's ENABLED
            ks_status = KillswitchStatusEnum.DISABLED

        raw_dict = {
            ConnectionStatusEnum.SERVER_INFORMATION: server_information_dict,
            ConnectionStatusEnum.PROTOCOL: ProtocolEnum(protocol),
            ConnectionStatusEnum.KILLSWITCH: ks_status,
            ConnectionStatusEnum.TIME: connected_time,
            ConnectionStatusEnum.NETSHIELD: self.user_settings._get_netshield(), # noqa
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

        # Public method providade by user_settings
        ks_user_setting = self.user_settings._get_killswitch()

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
