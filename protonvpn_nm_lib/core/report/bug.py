import datetime
import os
import re

from ...constants import (NETWORK_MANAGER_LOGFILE, PROTON_XDG_CACHE_HOME_LOGS,
                          PROTONVPN_RECONNECT_LOGFILE)
from ..subprocess_wrapper import subprocess
from ..utils import Singleton


class BugReport(metaclass=Singleton):
    DELTA_TIME_IN_DAYS = 3
    COMPILED_LOG_EPOCH_RE = re.compile(r"(\[\d+\.\d+\])")
    IS_USER_UNIT = False

    def generate_logs(self):
        """Generate all logs."""
        self.generate_network_manager_log()
        self.generate_protonvpn_reconnector_log()

    def generate_network_manager_log(self):
        """Generate NetworkManager log file for bug report.

        The log file is created with the help of python-systemd
        package which can easily read journalctl content.
        """
        self._remove_network_manager_log_if_exists()
        self.IS_USER_UNIT = False
        self.__generate_log("NetworkManager.service", NETWORK_MANAGER_LOGFILE)

    def generate_protonvpn_reconnector_log(self):
        """Generate ProtonVPN Reconnect log file for bug report.

        The log file is created with the help of python-systemd
        package which can easily read journalctl content.
        """
        self._remove_protonvpn_reconnect_log_if_exists()
        self.IS_USER_UNIT = True
        self.__generate_log("protonvpn_reconnect.service", PROTONVPN_RECONNECT_LOGFILE)

    def _remove_network_manager_log_if_exists(self):
        self.__remove_log_if_exists(NETWORK_MANAGER_LOGFILE)

    def _remove_protonvpn_reconnect_log_if_exists(self):
        self.__remove_log_if_exists(PROTONVPN_RECONNECT_LOGFILE)

    def __generate_log(self, systemd_unit, filepath):
        """Generate log file.

        Args:
            systemd_unit (string): systemd .service name
            filepath (string): filepath to log file
        """
        from systemd import journal

        _journal = journal.Reader()

        if self.IS_USER_UNIT:
            _journal.add_match(_SYSTEMD_USER_UNIT=systemd_unit)
        else:
            _journal.add_match(_SYSTEMD_UNIT=systemd_unit)

        _journal.log_level(journal.LOG_DEBUG)

        self.__add_log_to_file(_journal, filepath)

        _journal.close()

    def __remove_log_if_exists(self, filepath):
        """Remove log file if it exists.

        Args:
            filepath (string): filepath to log file
        """
        if os.path.isfile(filepath):
            os.remove(filepath)

    def __add_log_to_file(self, journal, filepath):
        """Add log entry to file, line by line.

        The log fil will contain information from the last 3 days.

        Args:
            journal (systemd.journal.Reader): journal reader object
            filepath (string): filepath to log file
        """
        start_date = datetime.datetime.today() - datetime.timedelta(
            days=self.DELTA_TIME_IN_DAYS
        )
        with open(filepath, "a") as f:
            for entry in journal:
                try:
                    if entry["_SOURCE_REALTIME_TIMESTAMP"] < start_date:
                        continue
                except KeyError:
                    if entry["__REALTIME_TIMESTAMP"] < start_date:
                        continue

                f.write(self.__format_entry(entry))

    def __format_entry(self, entry):
        """Format log entry.

        It will also remove the time in epoch and replace it by human redeable time.

        Args:
            entry (dict): entry containing journalctl data
        """
        try:
            _date = str(entry["_SOURCE_REALTIME_TIMESTAMP"])
            _msg = self.COMPILED_LOG_EPOCH_RE.sub("", entry["MESSAGE"])
        except KeyError:
            _date = str(entry["__REALTIME_TIMESTAMP"])
            _msg = entry["MESSAGE"]

        _entry = _date + " " + _msg + "\n"

        return _entry

    def open_folder_with_logs(self):
        subprocess.run(["xdg-open", PROTON_XDG_CACHE_HOME_LOGS])
