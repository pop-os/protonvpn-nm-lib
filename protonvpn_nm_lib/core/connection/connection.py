from .connection_adapter import ConnectionAdapter
from ...enums import MetadataEnum, KillSwitchActionEnum, KillswitchStatusEnum
from ... import exceptions
from ...logger import logger


class Connection:
    def __init__(self, adapter=ConnectionAdapter()):
        self.adapter = adapter
        self.ipv6_lp = None
        self.killswitch = None
        self.protonvpn_user = None
        self.connection_metadata = None
        self.daemon_reconnector = None

    def get_non_active_protonvpn_connection(self):
        return self.adapter.get_non_active_protonvpn_connection()

    def get_active_protonvpn_connection(self):
        return self.adapter.get_active_protonvpn_connection()

    def setup_connection(self, server_data, user_data):
        domain = server_data.get("domain")
        servername = server_data.get("servername")
        server_entry_ip = server_data.get("server_entry_ip")

        dns = user_data.get("dns")
        credentials = user_data.get("credentials")

        kwargs = {
            "user_data": {
                "username": credentials.get("ovpn_username"),
                "password": credentials.get("ovpn_password")
            },
            "domain": domain,
            "servername": servername,
            "dns": {
                "dns_status": dns.get("dns_status"),
                "custom_dns": dns.get("dns_ip_list")
            }
        }
        self._pre_setup_connection(server_entry_ip)
        self.adapter.vpn_add_connection(**kwargs)

    def connect(self):
        self.adapter.vpn_connect()
        self.connection_metadata.save_connected_time()

    def disconnect(self):
        try:
            self.adapter.vpn_remove_connection()
        except exceptions.ConnectionNotFound as e:
            raise exceptions.ConnectionNotFound(
                "Unable to disconnect: {}".format(e)
            )
        except (
            exceptions.RemoveConnectionFinishError,
            exceptions.StopConnectionFinishError
        ) as e:
            raise exceptions.ConnectionNotFound(
                "Unable to disconnect: {}".format(e)
            )
        except (
            exceptions.ProtonVPNException,
            # TO-DO: to be wrapped, as we shouldn't know if dbus is being used
            # or something else.
            # dbus.exceptions.DBusException,
            Exception
        ) as e:
            logger.exception(
                "Unknown error: {}".format(e)
            )
            raise Exception("Unknown error occured: {}".format(e))

        logger.info("Disconnected from VPN.")
        self.connection_metadata.remove_connection_metadata(
            MetadataEnum.CONNECTION
        )
        logger.info("Removing connection metadata.")
        self._post_disconnect()

    # TO-DO: Maybe move code below outside of this class
    def _pre_setup_connection(self, entry_ip):
        logger.info("Running pre-setup connection.")
        if self.ipv6_lp.enable_ipv6_leak_protection:
            self.ipv6_lp.manage(KillSwitchActionEnum.ENABLE)
        if self.protonvpn_user.settings.killswitch == KillswitchStatusEnum.HARD: # noqa
            self.killswitch.manage(
                KillSwitchActionEnum.PRE_CONNECTION,
                server_ip=entry_ip
            )

    # TO-DO: Maybe move code below outside of this class
    def _post_disconnect(self):
        logger.info("Running post disconnect.")
        self.daemon_reconnector.stop_daemon_reconnector()
        self.ipv6_lp.manage(KillSwitchActionEnum.DISABLE)
        if self.protonvpn_user.settings.killswitch == KillswitchStatusEnum.SOFT: # noqa
            self.killswitch.manage(KillSwitchActionEnum.DISABLE)
