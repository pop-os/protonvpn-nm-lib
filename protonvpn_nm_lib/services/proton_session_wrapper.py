import inspect
import random
import re
import time
import requests
from proton.api import ProtonError, Session

from .. import exceptions
from ..enums import ProtonSessionAPIMethodEnum
from ..logger import logger


class ProtonSessionWrapper(object):
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
    API_METHODS = [
        ProtonSessionAPIMethodEnum.API_REQUEST,
        ProtonSessionAPIMethodEnum.AUTHENTICATE,
        ProtonSessionAPIMethodEnum.LOGOUT
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

        if method == ProtonSessionAPIMethodEnum.API_REQUEST:
            return self.api_request(*args, **kwargs)
        elif method == ProtonSessionAPIMethodEnum.AUTHENTICATE:
            return self.authenticate(*args, **kwargs)
        elif method == ProtonSessionAPIMethodEnum.LOGOUT:
            return self.logout()

    def check_method_exists(self, method):
        if method not in self.API_METHODS:
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

        api_methods = {
            ProtonSessionAPIMethodEnum.API_REQUEST: self.proton_session.api_request, # noqa
            ProtonSessionAPIMethodEnum.AUTHENTICATE: self.proton_session.authenticate, # noqa
            ProtonSessionAPIMethodEnum.LOGOUT: self.proton_session.logout,
        }

        error = False
        api_response = False
        logger.info(
            "Method: {} - {}".format(
                method, api_methods[method]
            )
        )

        try:
            api_response = api_methods[method](
                *args, **api_kwargs
            )
        except ProtonError as e:
            error = e
        except requests.exceptions.ConnectTimeout as e:
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
