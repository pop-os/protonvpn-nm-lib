import datetime
import inspect
import json
import random
import re
import time

import requests
from proton.api import ProtonError, Session

from .. import exceptions
from ..constants import CACHED_SERVERLIST
from ..enums import (MetadataActionEnum, MetadataEnum,
                     ProtonSessionAPIMethodEnum)
from ..logger import logger
from .metadata_manager import MetadataManager


class ProtonSessionWrapper(MetadataManager):
    """Proton-client wrapper for improved error handling.

    If any HTTP status code is to be managed in a specific way,
    then a method with the prefix "handle_x" has to be created,
    where "x" represent the HTTP status code that is to be specifically
    managed. If a HTTP status code is not to be handled in a specific way,
    then it is enough to provide then status code in the HTTPS_STATUS_CODES.
    If a custom exception is needed for exception handling then that should be
    added to the exceptions.py file. This class searches for a matching
    exception in exceptions.py, thus, a matching exception can be created,
    otherwise UnhandledAPIError is asssigned to that status code.
    """
    proton_session = False
    HTTPS_STATUS_CODES = [
        400, 401, 403, 404, 409,
        422, 429, 500, 501, 503,
        5002, 5003, 8002, 85032,
        10013
    ]
    API_CALL_TYPES = [
        ProtonSessionAPIMethodEnum.API_REQUEST,
        ProtonSessionAPIMethodEnum.AUTHENTICATE,
        ProtonSessionAPIMethodEnum.LOGOUT,
        ProtonSessionAPIMethodEnum.FULL_CACHE,
        ProtonSessionAPIMethodEnum.LOADS_CACHE
    ]
    HTTP_STATUS_EXCEPTIONS = {}
    HTTP_STATUS_ERROR_HANDLERS = {}

    def __init__(
        self, **kwargs
    ):
        self.setup_error_handling("handle_known_status")
        self.setup_exception_handling()
        self.user_manager = kwargs.pop("user_manager")
        self.proton_session = Session(**kwargs)


    def api_request(self, *args, **api_kwargs):
        """Wrapper for proton-client api_request.

        Args:
            Takes same arguments as proton-client.
        """
        logger.info("API Call: {} - {}".format(args, api_kwargs))
        api_response, error = self.call_api_method(
            ProtonSessionAPIMethodEnum.API_REQUEST,
            *args,
            **api_kwargs
        )
        if not error:
            return api_response

        return self.exception_manager(
            error, ProtonSessionAPIMethodEnum.API_REQUEST, *args, **api_kwargs
        )

    def authenticate(self, username, password):
        """"Proxymethod for proton-client authenticate.

        Args:
            username (string): protonvpn username
            password (string): protonvpn password
        """
        logger.info("Authenticating user")
        api_response, error = self.call_api_method(
            ProtonSessionAPIMethodEnum.AUTHENTICATE,
            username, password
        )
        if not error:
            return api_response

        return self.exception_manager(
            error, ProtonSessionAPIMethodEnum.AUTHENTICATE, username, password
        )

    def cache_servers(self):
        """"Cache servers."""
        full_cache_time_expire = 180
        loads_cache_time_expire = 15
        if not self.check_metadata_exists(MetadataEnum.SERVER_CACHE):
            self.full_cache()
            return

        cache_metadata = self.manage_metadata(
            MetadataActionEnum.GET, MetadataEnum.SERVER_CACHE
        )

        full_cache_time = self.convert_time(
            int(cache_metadata["full_cache_timestamp"])
        )
        loads_cache_time = self.convert_time(
            int(cache_metadata["loads_cache_timestamp"])
        )

        next_full_cache_time = full_cache_time + datetime.timedelta(
            minutes=full_cache_time_expire
        )
        next_loads_cache_time = loads_cache_time + datetime.timedelta(
            minutes=loads_cache_time_expire
        )
        now_time = self.convert_time(time.time())

        if now_time >= next_full_cache_time:
            self.full_cache()
        elif now_time >= next_loads_cache_time:
            self.loads_cache()

    def full_cache(self):
        """Full servers cache."""
        logger.info("Caching full servers")
        api_response, error = self.call_api_method(
            ProtonSessionAPIMethodEnum.FULL_CACHE,
            "/vpn/logicals"
        )
        if not error:
            metadata = {
                "full_cache_timestamp": str(int(time.time())),
                "loads_cache_timestamp": str(int(time.time()))
            }
            self.manage_metadata(
                MetadataActionEnum.WRITE,
                MetadataEnum.SERVER_CACHE,
                metadata
            )
            self.store_server_cache(api_response, full_cache=True)
            return

        return self.exception_manager(
            error, ProtonSessionAPIMethodEnum.FULL_CACHE
        )

    def loads_cache(self):
        """Cache server loads."""
        logger.info("Caching server loads")
        api_response, error = self.call_api_method(
            ProtonSessionAPIMethodEnum.FULL_CACHE,
            "/vpn/loads"
        )
        if not error:
            metadata = self.manage_metadata(
                MetadataActionEnum.GET, MetadataEnum.SERVER_CACHE
            )
            metadata["loads_cache_timestamp"] = str(int(time.time()))
            self.manage_metadata(
                MetadataActionEnum.WRITE,
                MetadataEnum.SERVER_CACHE,
                metadata
            )
            self.store_server_cache(api_response)
            return

        return self.exception_manager(
            error, ProtonSessionAPIMethodEnum.FULL_CACHE
        )

    def store_server_cache(
        self, cache, full_cache=False, cache_path=CACHED_SERVERLIST
    ):
        if full_cache:
            with open(cache_path, "w") as f:
                json.dump(cache, f)
            return

        with open(cache_path, "r") as f:
            servers = json.load(f)

        cache_dict = {v["ID"]: v for v in cache["LogicalServers"]}

        for server in servers["LogicalServers"]:
            if server["ID"] in cache_dict:
                new_value = cache_dict.pop(server["ID"])
                server["Load"] = new_value["Load"]
                server["Score"] = new_value["Score"]

        self.store_server_cache(servers, full_cache=True)

    def yield_server_list(self, server_list):
        for server in server_list["LogicalServers"]:
            yield server

    def logout(self):
        """"Proxymethod for proton-client logout."""
        logger.info("Loggging out user")
        api_response, error = self.call_api_method(
            ProtonSessionAPIMethodEnum.LOGOUT
        )
        if not error:
            return api_response

        return self.exception_manager(
            error, ProtonSessionAPIMethodEnum.LOGOUT
        )

    @staticmethod
    def load(dump, user_manager, TLSPinning=True):
        """Wrapper for proton-client load."""
        api_url = dump['api_url']
        appversion = dump['appversion']
        user_agent = dump['User-Agent']
        proton_session_wrapper = ProtonSessionWrapper(
            api_url=api_url,
            appversion=appversion,
            user_agent=user_agent,
            TLSPinning=TLSPinning,
            user_manager=user_manager
        )

        proton_session_wrapper.proton_session = Session.load(
            dump, TLSPinning=True
        )
        return proton_session_wrapper

    def dump(self):
        """Proxymethod for proton-client dump."""
        return self.proton_session.dump()

    def convert_time(self, epoch_time, return_full_date=True):
        """Convert time from epoch to 24h.

        Args:
            epoch_time (string): time in seconds since epoch
            return_full_date: whether to return full date and time

        Returns:
            string: YYYY-MM-dd hh:mm:ss (when) | hh:mm:ss (time since)
        """
        if return_full_date:
            return datetime.datetime.fromtimestamp(epoch_time)

        time_since = (
            time.time()
            - int(epoch_time)
        )

        return str(
            datetime.timedelta(
                seconds=time_since
            )
        ).split(".")[0]

    def flatten_tuple(self, _tuple):
        """Recursively flatten tuples."""
        if not isinstance(_tuple, tuple):
            return (_tuple,)
        elif len(_tuple) == 0:
            return ()
        elif isinstance(_tuple[0], dict):
            return self.flatten_tuple(_tuple[1:])
        else:
            return self.flatten_tuple(_tuple[0]) \
                + self.flatten_tuple(_tuple[1:])

    def handle_known_status(self, error, method, *_, **__):
        logger.info("Catched \"{}\" error".format(error))
        error_code = error.code
        if error_code not in self.HTTP_STATUS_EXCEPTIONS:
            raise exceptions.UnhandledAPIError(error)

        raise self.HTTP_STATUS_EXCEPTIONS[error.code](error.error)

    def handle_401(self, error, method, *args, **kwargs):
        """Handles access token expiration."""
        logger.info("Catched 401 error, refreshing session data")
        self.check_method_exists(method)

        try:
            self.proton_session.refresh()
        except Exception as e:
            return self.handle_known_status(e, method, args, kwargs)

        # Store session data
        logger.info("Storing new session data")
        self.user_manager.store_data(
            self.proton_session.dump(),
            self.user_manager.keyring_sessiondata,
            self.user_manager.keyring_service
        )

        return self.get_method(method, args, kwargs)

    def handle_429(self, error, method, *args, **kwargs):
        logger.info("Catched 429 error, will retry")
        self.check_method_exists(method)

        hold_request_time = error.headers["Retry-After"]
        try:
            hold_request_time = int(hold_request_time)
        except ValueError:
            hold_request_time = random.randint(0, 20)
        logger.info("Retrying after {} seconds".format(hold_request_time))
        time.sleep(hold_request_time)

        return self.get_method(method, args, kwargs)

    def handle_503(self, error, method, *args, **kwargs):
        logger.info("Catched 503 error, retrying new request")
        self.check_method_exists(method)
        return self.get_method(method, args, kwargs)

    def get_method(self, method, *args, **kwargs):
        logger.info("Calling {}".format(method))

        if (
            method == ProtonSessionAPIMethodEnum.API_REQUEST
            or method == ProtonSessionAPIMethodEnum.FULL_CACHE
            or method == ProtonSessionAPIMethodEnum.LOADS_CACHE
        ):
            return self.api_request(*args, **kwargs)
        elif method == ProtonSessionAPIMethodEnum.AUTHENTICATE:
            return self.authenticate(*args, **kwargs)
        elif method == ProtonSessionAPIMethodEnum.LOGOUT:
            return self.logout()

    def check_method_exists(self, method):
        if method not in self.API_CALL_TYPES:
            logger.error(
                "[!] UnhandledAPIMethod: Unknown \"{}\" method. "
                " Raising exception.".format(method)
            )
            raise exceptions.UnhandledAPIMethod(
                "The specified method \"{}\""
                "is unhandled/unknown".format(method)
            )

    def call_api_method(self, method, *args, **api_kwargs):
        """Calls appropriate API method.

        Args:
            method (ProtonSessionAPIMethodEnum): object
        Returns:
            Tuple with api_reponse and error
        """
        self.check_method_exists(method)
        args = self.flatten_tuple(args)

        self.api_methods = {
            ProtonSessionAPIMethodEnum.API_REQUEST: self.proton_session.api_request, # noqa
            ProtonSessionAPIMethodEnum.AUTHENTICATE: self.proton_session.authenticate, # noqa
            ProtonSessionAPIMethodEnum.LOGOUT: self.proton_session.logout,
            ProtonSessionAPIMethodEnum.FULL_CACHE: self.proton_session.api_request, # noqa
            ProtonSessionAPIMethodEnum.LOADS_CACHE: self.proton_session.api_request, # noqa
        }

        error = False
        api_response = False
        logger.info(
            "Method: {} - {}".format(
                method, self.api_methods[method]
            )
        )

        try:
            api_response = self.api_methods[method](
                *args, **api_kwargs
            )
        except ProtonError as e:
            logger.exception("[!] ProtonError: {}".format(e))
            error = e
        except requests.exceptions.Timeout as e:
            logger.exception("[!] APITimeoutError: {}".format(e))
            raise exceptions.APITimeoutError(e)
        except Exception as e:
            logger.exception(
                "[!] ProtonSessionAPIError: {}. Raising exception.".format(e)
            )
            raise exceptions.ProtonSessionAPIError(
                "ProtonSessionAPIError: {}".format(e)
            )

        return api_response, error

    def exception_manager(self, error, method, *args, **api_kwargs):
        """Handle exceptions according to error.

        Args:
            error (tuple): proton.api.ProtonError exception
            method (ProtonSessionAPIMethodEnum): object
        Returns:
            Either response of error code in HTTPS_STATUS_CODES
            or raises exception.
        """
        if error.code not in self.HTTP_STATUS_ERROR_HANDLERS:
            logger.exception(
                "[!] UnhandledAPIError: {}. Raising exception".format(error)
            )
            raise exceptions.UnhandledAPIError(
                "{}".format(error.error)
            )

        return self.HTTP_STATUS_ERROR_HANDLERS[error.code](
            error, method,
            args, **api_kwargs
        )

    def setup_error_handling(self, generic_handler_method_name):
        """Setup automatic error handling.

        All API handler methods should start with "handle_" and
        then the number of the HTTP status that is to be handled.
        The rest is taked care of by the code.

        Args:
            generic_handler_method_name (string):
                name of the generic handler method
        """
        logger.info("Setting up error handling")
        existing_handler_methods = {}
        generic_handler_method = None
        re_api_status_code = re.compile(
            r"^([A-Za-z_]+)(\d+)$"
        )
        for class_member in inspect.getmembers(self):
            result = re_api_status_code.search(class_member[0])

            if (
                not generic_handler_method
                and generic_handler_method_name == class_member[0]
            ):
                generic_handler_method = class_member[1]

            if result:
                err_num = int(result.groups()[1])
                if err_num in self.HTTPS_STATUS_CODES:
                    existing_handler_methods[err_num] = class_member[1]

        yield_https_status_codes = self.yield_https_status_codes()

        for err_num in yield_https_status_codes:
            if err_num not in existing_handler_methods:
                self.HTTP_STATUS_ERROR_HANDLERS[err_num] = generic_handler_method # noqa
                continue

            self.HTTP_STATUS_ERROR_HANDLERS[err_num] = existing_handler_methods[err_num] # noqa

    def setup_exception_handling(self):
        """Setup automatic exception handling.

        Searches for exceptions in exceptions.py with matching
        exception errors via regex. It either assigns the matching
        exception or assings a generic exception (APIError).
        """
        logger.info("Setting up exception handling")
        existing_exceptions = {}
        re_api_status_code = re.compile(
            r"^([A-Za-z]+)(\d{3,})([A-Za-z]+)$"
        )
        for class_member in inspect.getmembers(exceptions):
            result = re_api_status_code.search(class_member[0])
            if result:
                err_num = int(result.groups()[1])
                if err_num in self.HTTPS_STATUS_CODES:
                    existing_exceptions[err_num] = class_member[1]

        yield_https_status_codes = self.yield_https_status_codes()

        for err_num in yield_https_status_codes:
            if err_num not in existing_exceptions:
                self.HTTP_STATUS_EXCEPTIONS[err_num] = exceptions.APIError
                continue

            self.HTTP_STATUS_EXCEPTIONS[err_num] = existing_exceptions[err_num] # noqa

    def yield_https_status_codes(self):
        for err_num in self.HTTPS_STATUS_CODES:
            yield err_num
