import os
import subprocess
import sys

from dialog import Dialog

from lib.constants import ProtocolEnum, SUPPORTED_FEATURES
from lib.logger import logger


def dialog(server_manager, session):
    """Connect to a server with a dialog menu."""
    def show_dialog(headline, choices, stop=False):
        """Show the dialog and process response."""
        d = Dialog(dialog="dialog")

        code, tag = d.menu(headline, title="ProtonVPN-CLI", choices=choices)
        if code == "ok":
            return tag
        else:
            os.system("clear")
            print("Canceled.")
            sys.exit(1)

    # Check if dialog is installed
    dialog_check = subprocess.run(['which', 'dialog'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
    if not dialog_check.returncode == 0:
        print("'dialog' not found. "
              "Please install dialog via your package manager.")
        sys.exit(1)

    server_manager.cache_servers(session)

    server_tiers = {0: "F", 1: "B", 2: "P"}

    servers = server_manager.filter_servers(session)

    countries = {}
    for server in servers:
        country = server_manager.extract_country_name(server["ExitCountry"])
        if country not in countries.keys():
            countries[country] = []
        countries[country].append(server["Name"])

    # Fist dialog
    choices = []

    for country in sorted(countries.keys()):
        country_features = []
        for server in countries[country]:
            feat = int(server_manager.extract_server_value(
                server, "Features", servers)
            )
            if not SUPPORTED_FEATURES[feat] in country_features:
                country_features.append(SUPPORTED_FEATURES[feat])
        choices.append((country, " | ".join(sorted(country_features))))

    country = show_dialog("Choose a country:", choices)

    # Second dialog
    # lambda sorts servers by Load instead of name
    choices = []
    country_servers = sorted(countries[country],
                             key=lambda s: server_manager.extract_server_value(
                                 s, "Load", servers))

    for servername in country_servers:

        load = str(
            server_manager.extract_server_value(servername, "Load", servers)
        ).rjust(3, " ")

        feature = SUPPORTED_FEATURES[
            server_manager.extract_server_value(
                servername, 'Features', servers
            )
        ]

        tier = server_tiers[
            server_manager.extract_server_value(servername, "Tier", servers)
        ]

        choices.append((servername, "Load: {0}% | {1} | {2}".format(
            load, tier, feature
        )))

    server_result = show_dialog("Choose the server to connect:", choices)

    protocol_result = show_dialog(
        "Choose a protocol:", [
            (ProtocolEnum.UDP, "Better Speed"),
            (ProtocolEnum.TCP, "Better Reliability")
        ]
    )

    os.system("clear")
    return server_result, protocol_result
