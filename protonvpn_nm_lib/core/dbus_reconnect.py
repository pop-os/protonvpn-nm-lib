import os
from .subprocess_wrapper import subprocess
import sys

import protonvpn_nm_lib

from ..constants import (ENV_CI_NAME, LOCAL_SERVICE_FILEPATH, SERVICE_TEMPLATE,
                         XDG_CONFIG_SYSTEMD_USER)
from ..logger import logger
from ..enums import DaemonReconnectorEnum


class DbusReconnect:
    DAEMON_COMMANDS = [
        DaemonReconnectorEnum.START,
        DaemonReconnectorEnum.STOP,
        DaemonReconnectorEnum.DAEMON_RELOAD
    ]

    def __init__(self):
        if not os.path.isdir(XDG_CONFIG_SYSTEMD_USER):
            os.makedirs(XDG_CONFIG_SYSTEMD_USER)

        if not os.path.isfile(LOCAL_SERVICE_FILEPATH):
            self.setup_service()

    def setup_service(self):
        root_dir = os.path.dirname(protonvpn_nm_lib.__file__)
        daemon_folder = os.path.join(root_dir, "daemon")
        python_service_path = os.path.join(
            daemon_folder, "dbus_daemon_reconnector.py"
        )
        python_interpreter_path = sys.executable
        exec_start = python_interpreter_path + " " + python_service_path
        with_cli_path = SERVICE_TEMPLATE.replace("EXEC_START", exec_start)

        with open(LOCAL_SERVICE_FILEPATH, "w") as f:
            f.write(with_cli_path)

        self.call_daemon_reconnector(DaemonReconnectorEnum.DAEMON_RELOAD)

    def start_daemon_reconnector(self):
        """Start daemon reconnector."""
        daemon_status = False
        try:
            daemon_status = self.check_daemon_reconnector_status()
        except Exception as e:
            logger.exception("[!] Exception: {}".format(e))

        logger.info("Daemon status: {}".format(daemon_status))

        if daemon_status:
            return

        if not os.environ.get(ENV_CI_NAME):
            self.daemon_reconnector_manager(
                DaemonReconnectorEnum.START,
                daemon_status
            )

    def stop_daemon_reconnector(self):
        """Stop daemon reconnector."""
        daemon_status = False
        try:
            daemon_status = self.check_daemon_reconnector_status()
        except Exception as e:
            logger.exception("[!] Exception: {}".format(e))

        if not daemon_status:
            return

        logger.info("Daemon status: {}".format(daemon_status))
        if not os.environ.get(ENV_CI_NAME):
            self.daemon_reconnector_manager("stop", daemon_status)

    def daemon_reconnector_manager(self, callback_type, daemon_status):
        """Start/stop daemon reconnector.

        Args:
            callback_type (DaemonReconnectorEnum): enum
            daemon_status (int): 1 or 0
        """
        logger.info(
            "Managing daemon: cb_type-> \"{}\"; ".format(callback_type)
            + "daemon_status -> \"{}\"".format(daemon_status)
        )
        if callback_type == DaemonReconnectorEnum.START and not daemon_status:
            self.call_daemon_reconnector(callback_type)
        elif callback_type == DaemonReconnectorEnum.STOP and daemon_status:
            self.call_daemon_reconnector(callback_type)
            try:
                daemon_status = self.check_daemon_reconnector_status()
            except Exception as e:
                logger.exception("[!] Exception: {}".format(e))
            else:
                logger.info(
                    "Daemon status after stopping: {}".format(daemon_status)
                )

    def check_daemon_reconnector_status(self):
        """Checks the status of the daemon reconnector and starts the process
        only if it's not already running.

        Returns:
            int: indicates the status of the daemon process
        """
        logger.info("Checking daemon reconnector status")
        check_daemon = subprocess.run(
            ["systemctl", "status", "--user", "protonvpn_reconnect"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        decoded_stdout = check_daemon.stdout.decode()
        if (
            check_daemon.returncode == 3
        ):
            # Not running
            return 0
        elif (
            check_daemon.returncode == 0
        ):
            # Already running
            return 1
        else:
            # Service threw an exception
            raise Exception(
                "[!] An error occurred while checking for ProtonVPN "
                + "reconnector service: "
                + "(Return code: {}; Exception: {} {})".format(
                    check_daemon.returncode, decoded_stdout,
                    check_daemon.stderr.decode().strip("\n")
                )
            )

    def call_daemon_reconnector(
        self, command
    ):
        """Makes calls to daemon reconnector to either
        start or stop the process.

        Args:
            command (string): to either start or stop the process
        """
        logger.info("Calling daemon reconnector")
        if command not in self.DAEMON_COMMANDS:
            raise Exception("Invalid daemon command \"{}\"".format(command))

        call_daemon = subprocess.run(
            ["systemctl", command.value, "--user", "protonvpn_reconnect"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if command == DaemonReconnectorEnum.DAEMON_RELOAD:
            call_daemon = subprocess.run(
                [
                    "systemctl",
                    "--user",
                    DaemonReconnectorEnum.DAEMON_RELOAD.value
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        decoded_stdout = call_daemon.stdout.decode()
        decoded_stderr = call_daemon.stderr.decode().strip("\n")

        if not call_daemon.returncode == 0:
            msg = "[!] An error occurred while {}ing ProtonVPN "\
                "reconnector service: {} {}".format(
                    command,
                    decoded_stdout,
                    decoded_stderr
                )
            logger.error(msg)
