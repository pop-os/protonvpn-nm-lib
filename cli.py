import argparse
import getpass
import inspect
import sys

from cli_dialog import dialog
from lib import exceptions
from lib.services.certificate_manager import CertificateManager
from lib.services.connection_manager import ConnectionManager
from lib.services.server_manager import ServerManager
from lib.services.user_manager import UserManager
from lib.enums import ProtocolEnum


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

        try:
            protocol = args.protocol.lower().strip()
        except AttributeError:
            protocol = ProtocolEnum.TCP
        else:
            delattr(args, "protocol")

        try:
            session = self.user_manager.load_session()
        except (
            exceptions.JSONAuthDataNoneError,
            exceptions.JSONAuthDataEmptyError
        ):
            print("[!] No stored session was found, please try to first login")
            sys.exit(1)

        cli_commands = dict(
            servername=self.server_manager.direct,
            fastest=self.server_manager.fastest,
            random=self.server_manager.random_c,
            cc=self.server_manager.country_f,
            sc=self.server_manager.feature_f,
            p2p=self.server_manager.feature_f,
            tor=self.server_manager.feature_f,
        )

        command = False

        for cls_attr in inspect.getmembers(args):
            if cls_attr[0] in cli_commands and cls_attr[1]:
                command = list(cls_attr)

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
            username, password = self.user_manager.fetch_vpn_credentials()
        except (
            exceptions.JSONAuthDataNoneError, exceptions.JSONAuthDataEmptyError
        ) as e:
            print(
                "[!] The stored session might be corrupted, please re-login."
                + "\nException: {}".format(e))
            sys.exit(1)

        try:
            self.connection_manager.add_connection(
                certificate_filename, username,
                password, CertificateManager.delete_cached_certificate
            )
        except exceptions.ImportConnectionError as e:
            print(e)
        else:
            self.connection_manager.start_connection()
        finally:
            sys.exit(1)

    def d(self):
        self.disconnect()

    def disconnect(self):
        try:
            self.connection_manager.remove_connection()
        except exceptions.ConnectionNotFound as e:
            print("[!] {}".format(e))
        finally:
            sys.exit(1)

    def login(self):
        def ask_username_password():
            """Set the ProtonVPN Username and Password."""

            print()
            ovpn_username = input("Enter your ProtonVPN username: ")

            # Ask for the password and confirmation until both are the same
            while True:
                ovpn_password1 = getpass.getpass(
                    "Enter your ProtonVPN password: "
                )
                ovpn_password2 = getpass.getpass(
                    "Confirm your ProtonVPN password: "
                )

                if not ovpn_password1 == ovpn_password2:
                    print()
                    print("[!] The passwords do not match. Please try again.")
                    sys.exit(1)
                else:
                    break

            return ovpn_username, ovpn_password1

        try:
            self.user_manager.load_session()
        except (
            exceptions.JSONAuthDataNoneError,
            exceptions.JSONAuthDataEmptyError
        ):
            username, password = ask_username_password()
            try:
                self.user_manager.login(username, password)
            except (
                exceptions.IncorrectCredentialsError,
                exceptions.APIAuthenticationError,
                ValueError
            ) as exp:
                print("Unable to authenticate: {}".format(exp))
            else:
                print("\nLogin successful!")
        else:
            print("\nYou are already logged in!")
        finally:
            sys.exit(1)

    def logout(self):
        try:
            self.user_manager.delete_user_session()
        except Exception as e:
            print(e)
        else:
            print("Logout successful!")
        finally:
            sys.exit(1)


NetworkManagerPrototypeCLI()
