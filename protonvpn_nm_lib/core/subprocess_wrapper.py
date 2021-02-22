import subprocess as _subprocess
import os
from pwd import getpwuid
from grp import getgrgid


class SubprocessWrapper():
    """Subprocess wrapper.
    This should be used instead of directly reling on subprocess,
    as it assures that the specified executables are safe to use.

    Exposes method:
        run()

    Description:

    run()
        Takes the exact same arguments as subprocess.run(), as this
        is effectivtly a layer on top of subprocess.
    """

    __BIN_TO_SEARCH = ["nmcli", "systemctl", "clear"]
    PIPE = -1
    STDOUT = -2
    DEVNULL = -3

    def __init__(self):
        self.__PATHS_TO_SEARCH = []
        self.__get_protected_paths()

    def __get_protected_paths(self):
        """Gets only protected paths.

        It looks at the uid and gid of a given folder
        from PATH, and appends the folder to __PATHS_TO_SEARCH
        given that both gid and uid of a folder are 0 (root).
        """
        __PATHS_TO_SEARCH = os.environ["PATH"].split(":")
        for path in __PATHS_TO_SEARCH:
            stat_info = os.stat(path)
            if stat_info.st_uid == 0 and stat_info.st_gid == 0:
                self.__PATHS_TO_SEARCH.append(path)

    def __check_call(self, args):
        """Performs a security check.

        This method takes in the args from run, and collects the
        binaries that are specified in there, assuring that
        only those binaries that are allowed in __BIN_TO_SEARCH
        are to be searched for. If user provides any other type of executable
        then the method will throw a LookupError.

        It then ensures that the file/binary is owned by root, by
        invoking __ensure_file_is_owned_by_root.
        """
        match_bin_collection = []
        for bin_to_search in self.__BIN_TO_SEARCH:
            if bin_to_search in args[0]:
                match_bin_collection.append(bin_to_search)

        if (match_bin_collection) == 0:
            raise LookupError(
                "No binaries were found, "
                "please provide specific only the allowed binaries: {}".format(
                    self.__BIN_TO_SEARCH)
            )

        for path in self.__PATHS_TO_SEARCH:
            for root, dirs, files in os.walk(path):
                for matched_bin_name in match_bin_collection:
                    if matched_bin_name in files:
                        self.__ensure_file_is_owned_by_root(
                            os.path.join(root, matched_bin_name)
                        )

    def __ensure_file_is_owned_by_root(self, filepath):
        """Ensures that file is owned by root.

        This method checks of the uid and gid of the file.
        If both are 0, then the file belongs to root as should
        be considered safe to use. Of course this does not cover
        the situation where root could be compromised.
        """
        user_id = getpwuid(os.stat(filepath).st_gid).pw_uid
        group_id = getgrgid(os.stat(filepath).st_gid).gr_gid

        if group_id != 0 and user_id != 0:
            raise Exception("Executable was not found")

    def run(
        self, *popenargs, input=None, capture_output=False,
        timeout=None, check=False, **kwargs
    ):
        if len(popenargs) == 0:
            raise TypeError("missing 1 required positional argument: 'args'")

        self.__check_call(popenargs)
        return _subprocess.run(
            *popenargs,
            capture_output=capture_output,
            timeout=timeout,
            check=check,
            **kwargs
        )

subprocess = SubprocessWrapper() # noqa
