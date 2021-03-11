from getpass import getuser

from ... import exceptions
from ...constants import CONFIG_STATUSES
from ...enums import (ConnectionMetadataEnum, MetadataEnum,
                      UserSettingStatusEnum)
from ...logger import logger


class SetupConnection:

    def __init__(self):
        self.virtual_device_name = None
        self.certificate_filepath = None

        self.connection = None
        self._vpn_settings = None
        self._conn_settings = None

    @staticmethod
    def init(
        protonvpn_user, physical_server,
        virtual_device_name,
        certificate_filepath
    ):
        setup_connection = SetupConnection()
        setup_connection.protonvpn_user = protonvpn_user
        setup_connection.physical_server = physical_server
        setup_connection.virtual_device_name = virtual_device_name
        setup_connection.certificate_filepath = certificate_filepath

        return setup_connection

    def run_setup(self, **kwargs):
        user_data = kwargs.get("user_data")
        self.username = user_data.get("username")
        self.password = user_data.get("password")

        self.domain = kwargs.get("domain")
        self.servername = kwargs.get("servername")

        dns = kwargs.get("dns")
        self.dns_status = dns.get("dns_status")
        self.custom_dns = dns.get("custom_dns")

        self._vpn_settings = self.connection.get_setting_vpn()
        self._conn_settings = self.connection.get_setting_connection()

        self.make_vpn_user_owned()
        self.set_custom_connection_id()
        self.add_vpn_credentials()
        self.add_server_certificate_check()
        self.apply_virtual_device_type()
        self.dns_configurator()

    def make_vpn_user_owned(self):
        # returns NM.SettingConnection
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/SettingConnection.html#NM.SettingConnection
        logger.info("Making VPN connection be user owned")
        self._conn_settings.add_permission(
            "user",
            getuser(),
            None
        )

    def set_custom_connection_id(self):
        self._conn_settings.props.id = "ProtonVPN " + self.servername

    def add_vpn_credentials(self):
        """Add OpenVPN credentials to ProtonVPN connection.

        Args:
            openvpn_username (string): openvpn/ikev2 username
            openvpn_password (string): openvpn/ikev2 password
        """
        # returns NM.SettingVpn if the connection contains one, otherwise None
        # https://lazka.github.io/pgi-docs/NM-1.0/classes/SettingVpn.html
        logger.info("Adding OpenVPN credentials")
        try:
            self._vpn_settings.add_data_item(
                "username", self.username
            )
            self._vpn_settings.add_secret(
                "password", self.password
            )
        except Exception as e:
            logger.exception(
                "AddConnectionCredentialsError: {}. ".format(e)
                + "Raising exception."
            )
            # capture_exception(e)
            raise exceptions.AddConnectionCredentialsError(e)

    def add_server_certificate_check(self):
        logger.info("Adding server certificate check")
        logger.debug("Server domain: {}".format(self.domain))
        appened_domain = "name:" + self.domain
        try:
            self._vpn_settings.add_data_item(
                "verify-x509-name", appened_domain
            )
        except Exception as e:
            logger.exception(
                "AddServerCertificateCheckError: {}. ".format(e)
                + "Raising exception."
            )
            # capture_exception(e)
            raise exceptions.AddServerCertificateCheckError(e)

    def apply_virtual_device_type(self):
        """Apply virtual device type and name."""
        logger.info("Applying virtual device type to VPN")
        virtual_device_type = self.extract_virtual_device_type(
            self.certificate_filepath
        )

        # Changes virtual tunnel name
        self._vpn_settings.add_data_item("dev", self.virtual_device_name)
        self._vpn_settings.add_data_item("dev-type", virtual_device_type)

    def extract_virtual_device_type(self, filename):
        """Extract virtual device type from .ovpn file.

        Args:
            filename (string): path to cached certificate
        Returns:
            string: "tap" or "tun", otherwise raises exception
        """
        logger.info("Extracting virtual device type")
        virtual_dev_type_list = ["tun", "tap"]

        with open(filename, "r") as f:
            content_list = f.readlines()
            dev_type = [dev.rstrip() for dev in content_list if "dev" in dev]

            try:
                dev_type = dev_type[0].split()[1]
            except IndexError as e:
                logger.exception("VirtualDeviceNotFound: {}".format(e))
                raise exceptions.VirtualDeviceNotFound(
                    "No virtual device type was specified in .ovpn file"
                )
            except Exception as e:
                logger.exception("Unknown exception: {}".format(e))
                # capture_exception(e)

            try:
                index = virtual_dev_type_list.index(dev_type)
            except (ValueError, KeyError, TypeError) as e:
                logger.exception("IllegalVirtualDevice: {}".format(e))
                raise exceptions.IllegalVirtualDevice(
                    "Only {} are permitted, though \"{}\" ".format(
                        ' and '.join(virtual_dev_type_list), dev_type
                    ) + " was provided"
                )
            except Exception as e:
                logger.exception("Unknown exception: {}".format(e))
                # capture_exception(e)
            else:
                return virtual_dev_type_list[index]

    def dns_configurator(self):
        """Apply dns configurations to ProtonVPN connection.

        Args:
            dns_setting (tuple(int, [])): contains dns configurations
        """
        logger.info("DNS configs: {} - {}".format(
            self.dns_status, self.custom_dns
        ))

        if self.dns_status not in CONFIG_STATUSES:
            raise Exception("Incorrect status configuration")

        dns_status = self.enforce_enbled_state_if_disabled()

        ipv4_config = self.connection.get_setting_ip4_config()
        ipv6_config = self.connection.get_setting_ip6_config()

        if dns_status == UserSettingStatusEnum.CUSTOM:
            self.apply_custom_dns_configuration(
                ipv4_config, ipv6_config
            )
            return

        self.apply_automatic_dns_configuration(
            ipv4_config, ipv6_config
        )

    def enforce_enbled_state_if_disabled(self):
        if self.dns_status == UserSettingStatusEnum.DISABLED:
            self.dns_status = UserSettingStatusEnum.ENABLED

    def apply_automatic_dns_configuration(self, ipv4_config, ipv6_config):
        logger.info("Applying automatic DNS")
        ipv4_config.props.dns_priority = -50
        ipv6_config.props.dns_priority = -50

    def apply_custom_dns_configuration(self, ipv4_config, ipv6_config):
        custom_dns = self.custom_dns
        ipv4_config.props.ignore_auto_dns = True
        ipv6_config.props.ignore_auto_dns = True

        logger.info("Applying custom DNS: {}".format(custom_dns))
        ipv4_config.props.dns_priority = -50
        ipv6_config.props.dns_priority = -50
        for ip in custom_dns:
            self.protonvpn_user.user_settings.\
                setting_configurator.is_valid_ip(ip)
        ipv4_config.props.dns = custom_dns
