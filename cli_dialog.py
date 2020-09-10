import os
import subprocess
import sys

from dialog import Dialog

from lib.constants import ProtocolEnum, SUPPORTED_FEATURES
from lib.logger import logger


def dialog(server_manager, session):
    """Connect to a server with a dialog menu."""

    # Check if dialog is installed
    dialog_check = subprocess.run(['which', 'dialog'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
    if not dialog_check.returncode == 0:
        print("'dialog' not found. "
              "Please install dialog via your package manager.")
        sys.exit(1)

    server_tiers = {0: "F", 1: "B", 2: "P"}
    server_manager.cache_servers(session)
    servers = server_manager.filter_servers(session)
    countries = generate_country_dict(server_manager, servers)

    # Fist dialog
    country = display_country(countries, server_manager, servers)

    # Second dialog
    server = display_servers(
        countries, server_manager,
        servers, country,
        server_tiers
    )

    protocol = display_protocol()

    os.system("clear")
    return server, protocol


def display_country(countries, server_manager, servers):
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

    return display_dialog("Choose a country:", choices)


def display_servers(countries, server_manager, servers, country, server_tiers):
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

    return display_dialog("Choose the server to connect:", choices)


def display_protocol():
    return display_dialog(
        "Choose a protocol:", [
            (ProtocolEnum.UDP, "Better Speed"),
            (ProtocolEnum.TCP, "Better Reliability")
        ]
    )


def display_dialog(headline, choices, stop=False):
    """Show the dialog and process response."""
    d = Dialog(dialog="dialog")

    code, tag = d.menu(headline, title="ProtonVPN-CLI", choices=choices)
    if code == "ok":
        return tag
    else:
        os.system("clear")
        print("Canceled.")
        sys.exit(1)


def generate_country_dict(server_manager, servers):
    countries = {}
    for server in servers:
        country = server_manager.extract_country_name(server["ExitCountry"])
        if country not in countries.keys():
            countries[country] = []
        countries[country].append(server["Name"])

    return countries
