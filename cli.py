import argparse
import getpass
import inspect
import sys

import sentry_sdk
from sentry_sdk import capture_exception  # noqa

from cli_dialog import dialog
from lib import exceptions
from lib.constants import APP_VERSION
from lib.enums import ProtocolEnum
from lib.logger import logger
from lib.services.certificate_manager import CertificateManager
from lib.services.connection_manager import ConnectionManager
from lib.services.server_manager import ServerManager
from lib.services.user_manager import UserManager

sentry_sdk.init(
    dsn="https://f9d7d18c83374b7a901f20036f8583e1@sentry.protontech.ch/62",
    release=APP_VERSION,
)


class NetworkManagerPrototypeCLI():
    connection_manager = ConnectionManager()
    user_manager = UserManager()
    server_manager = ServerManager(CertificateManager())

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("command", nargs="?")
        args = parser.parse_args(sys.argv[1:2])

        if not args.command or not hasattr(self, args.command):
            print(
                "python filename.py "
                + "[connect [<servername>|-f|-r|--p2p|--sc|--tor|--cc "
                + "<iso_country_code>] [-p] | disconnect | login | logout]"
            )
            parser.exit(1)

        logger.info("CLI command: {}".format(args))
        getattr(self, args.command)()

    def c(self):
        self.connect()

    def connect(self):
        parser = argparse.ArgumentParser(
            description="Connect to ProtonVPN", prog="protonvpn c"
        )
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "servername",
            nargs="?",
            help="Servername (CH#4, CH-US-1, HK5-Tor).",
            metavar=""
        )
        group.add_argument(
            "-f", "--fastest",
            help="Connect to the fastest ProtonVPN server.",
            action="store_true"
        )
        group.add_argument(
            "-r", "--random",
            help="Connect to a random ProtonVPN server.",
            action="store_true"
        )
        group.add_argument(
            "--cc",
            help="Connect to the specified country code (SE, PT, BR, AR).",
            metavar=""
        )
        group.add_argument(
            "--sc",
            help="Connect to the fastest Secure-Core server.",
            action="store_true"
        )
        group.add_argument(
            "--p2p",
            help="Connect to the fastest torrent server.",
            action="store_true"
        )
        group.add_argument(
            "--tor",
            help="Connect to the fastest Tor server.",
            action="store_true"
        )
        parser.add_argument(
            "-p", "--protocol", help="Connect via specified protocol.",
            choices=[
                ProtocolEnum.TCP,
                ProtocolEnum.UDP,
            ], metavar="", type=str.lower
        )

        args = parser.parse_args(sys.argv[2:])
        logger.info("Options: {}".format(args))
        command = False
        cli_commands = dict(
            servername=self.server_manager.direct,
            fastest=self.server_manager.fastest,
            random=self.server_manager.random_c,
            cc=self.server_manager.country_f,
            sc=self.server_manager.feature_f,
            p2p=self.server_manager.feature_f,
            tor=self.server_manager.feature_f,
        )
        exit_type = 1

        try:
            protocol = args.protocol.lower().strip()
        except AttributeError:
            protocol = ProtocolEnum.TCP
        else:
            delattr(args, "protocol")

        try:
            session = self.user_manager.load_session()
        except exceptions.JSONAuthDataEmptyError:
            print(
                "[!] The stored session might be corrupted, "
                + "please try to login again."
            )
            sys.exit(exit_type)
        except (
            exceptions.JSONAuthDataError,
            exceptions.JSONAuthDataNoneError
        ):
            print("[!] There is no stored sessio, please login first.")
            sys.exit(exit_type)
        except exceptions.AccessKeyringError:
            print(
                "[!] Unable to load session. Could not access keyring."
            )
            sys.exit(exit_type)
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error occured: {}.".format(e))
            sys.exit(exit_type)
        else:
            logger.info("Local session was found.")

        for cls_attr in inspect.getmembers(args):
            if cls_attr[0] in cli_commands and cls_attr[1]:
                command = list(cls_attr)

        logger.info("CLI connect type: {}".format(command))

        try:
            certificate_filename = cli_commands[command[0]](
                session, protocol, command
            )
        except TypeError:
            servername, protocol = dialog(
                self.server_manager,
                session,
            )

            certificate_filename = self.server_manager.direct(
                session, protocol, servername
            )

        try:
            openvpn_username, openvpn_password = self.user_manager.fetch_vpn_credentials( # noqa
                session
            )
        except exceptions.JSONAuthDataEmptyError:
            print(
                "[!] The stored session might be corrupted, "
                + "please try to login again."
            )
            sys.exit(exit_type)
        except (
            exceptions.JSONAuthDataError,
            exceptions.JSONAuthDataNoneError
        ):
            print("[!] There is no stored session, please login first.")
            sys.exit(exit_type)
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error occured: {}.".format(e))
            sys.exit(exit_type)

        logger.info("OpenVPN credentials were fetched.")

        try:
            self.connection_manager.add_connection(
                certificate_filename, openvpn_username,
                openvpn_password, CertificateManager.delete_cached_certificate
            )
        except exceptions.ImportConnectionError:
            print("An error occured upon importing connection.")
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error: {}".format(e))
            sys.exit(exit_type)
        else:
            exit_type = 0

        self.connection_manager.start_connection()
        sys.exit(exit_type)

    def d(self):
        self.disconnect()

    def disconnect(self):
        exit_type = 1
        try:
            self.connection_manager.remove_connection()
        except exceptions.ConnectionNotFound as e:
            print("[!] Unable to disconnect: {}".format(e))
        except (
            exceptions.RemoveConnectionFinishError,
            exceptions.StopConnectionFinishError
        ) as e:
            print("[!] Unable to disconnect: {}".format(e))
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error occured: {}".format(e))
        else:
            exit_type = 1
        finally:
            sys.exit(exit_type)

    def login(self):
        session_exists = False

        try:
            self.user_manager.load_session()
        except exceptions.JSONAuthDataEmptyError:
            print(
                "[!] The stored session might be corrupted, "
                + "please try to login again."
            )
            session_exists = False
        except (
            exceptions.JSONAuthDataError,
            exceptions.JSONAuthDataNoneError
        ):
            session_exists = False
        except exceptions.AccessKeyringError as e:
            print(
                "[!] Unable to load session. Could not access keyring: "
                + "{}".format(e)
            )
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error: {}".format(e))
        else:
            logger.info("User already logged in, local session was found.")
            session_exists = True

        if session_exists:
            print("\nYou are already logged in!")
            sys.exit()

        protonvpn_username = input("\nEnter your ProtonVPN username: ")
        protonvpn_password = getpass.getpass("Enter your ProtonVPN password: ")
        exit_type = 1

        try:
            self.user_manager.login(protonvpn_username, protonvpn_password)
        except (TypeError, ValueError) as e:
            print("[!] Unable to authenticate. {}".format(e))
        except exceptions.IncorrectCredentialsError:
            print(
                "[!] Unable to authenticate. "
                + "The provided credentials are incorrect"
            )
        except exceptions.APIAuthenticationError:
            print("[!] Unable to authenticate. Unexpected API response.")
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error occured: {}".format(e))
        else:
            exit_type = 0
            logger.info("Successful login.")
            print("\nLogin successful!")
        finally:
            sys.exit(exit_type)

    def logout(self):
        exit_type = 1

        try:
            self.user_manager.delete_user_session()
        except exceptions.StoredSessionNotFound:
            print("[!] Unable to logout. No session was found.")
        except exceptions.AccessKeyringError:
            print("[!] Unable to logout. Could not access keyring.")
        except Exception as e:
            capture_exception(e)
            logger.exception(
                "[!] Unknown error: {}".format(e)
            )
            print("[!] Unknown error occured: {}.".format(e))
        else:
            exit_type = 0
            logger.info("Successful logout.")
            print("Logout successful!")
        finally:
            sys.exit(exit_type)


NetworkManagerPrototypeCLI()
