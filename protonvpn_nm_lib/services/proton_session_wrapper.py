import inspect
import random
import re
import time

from proton.api import ProtonError, Session

from .. import exceptions
from ..logger import logger
from ..enums import ProtonSessionAPIMethodEnum


class ProtonSessionWrapper():
    """Proton-client wrapper for improved error handling.

    If any HTTP status code is to be managed in a specific way,
    then a method with the prefix "handle_x" has to be created,
    where "x" represent the HTTP status code that is to be specifically
    managed. This class also searches for a matching exception in
    exceptions.py, thus, a matching exception can be created,
    otherwise UnhandledAPIError is asssigned to that status code.
    """
    proton_session = False
    API_ERROR_LIST = [
        400, 401, 403, 404, 409,
        422, 429, 500, 501, 503,
        5002, 5003
    ]
    API_METHODS = [
        ProtonSessionAPIMethodEnum.API_REQUEST,
        ProtonSessionAPIMethodEnum.AUTHENTICATE,
        ProtonSessionAPIMethodEnum.LOGOUT
    ]
    API_EXCEPTION_DICT = {}
    ERROR_CODE_HANDLER = {}

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
        args = self.flatten_tuple(args)
        logger.info("API Call: {} - {}".format(args, api_kwargs))
        error = False
        try:
            api_response = self.proton_session.api_request(
                *args, **api_kwargs
            )
        except ProtonError as e:
            error = e
        except Exception as e:
            logger.exception(
                "[!] ProtonSessionAPIError: {}. Raising exception.".format(e)
            )
            raise exceptions.ProtonSessionAPIError(
                "ProtonSessionAPIError: {}".format(e)
            )

        if not error:
            return api_response

        try:
            result = self.ERROR_CODE_HANDLER[error.code](
                error, ProtonSessionAPIMethodEnum.API_REQUEST,
                args, **api_kwargs
            )
        except KeyError as e:
            logger.exception(
                "[!] UnhandledAPIError. {}. Raising exception".format(e)
            )
            raise exceptions.UnhandledAPIError(
                "Unhandled error: {}".format(e)
            )
        else:
            return result

    def authenticate(self, username, password):
        """"Proxymethod for proton-client authenticate.

        Args:
            username (string): protonvpn username
            password (string): protonvpn password
        """
        logger.info("Authenticating user")
        error = False

        try:
            self.proton_session.authenticate(username, password)
        except ProtonError as e:
            error = e
        except Exception as e:
            logger.exception(
                "[!] ProtonSessionAPIError: {}. Raising exception.".format(e)
            )
            raise exceptions.ProtonSessionAPIError(
                "ProtonSessionAPIError: {}".format(e)
            )

        if not error:
            return

        try:
            self.ERROR_CODE_HANDLER[error.code](
                error, ProtonSessionAPIMethodEnum.AUTHENTICATE,
                None, None
            )
        except KeyError as e:
            logger.exception(
                "[!] UnhandledAPIError. {}. Raising exception".format(e)
            )
            raise exceptions.UnhandledAPIError(
                "Unhandled error: {}".format(e)
            )

    def logout(self):
        """"Proxymethod for proton-client logout."""
        logger.info("Authenticating user")
        error = False

        try:
            self.proton_session.logout()
        except ProtonError as e:
            error = e
        except Exception as e:
            logger.exception(
                "[!] ProtonSessionWrapperError: {}."
                "Raising exception.".format(e)
            )
            raise exceptions.ProtonSessionWrapperError(
                "ProtonSessionWrapperError: {}".format(e)
            )

        if not error:
            return

        try:
            return self.ERROR_CODE_HANDLER[error.code](
                error, ProtonSessionAPIMethodEnum.LOGOUT,
                None, None
            )
        except KeyError as e:
            logger.exception(
                "[!] UnhandledAPIError. {}. Raising exception".format(e)
            )
            raise exceptions.UnhandledAPIError(
                "Unhandled error: {}".format(e)
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
        raise self.API_EXCEPTION_DICT[error.code](error.error)

    def handle_401(self, error, method, *args, **kwargs):
        """Handles access token expiration."""
        logger.info("Catched 401 error, refreshing session data")
        self.check_method_exists(method)

        self.proton_session.refresh()
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
                if err_num in self.API_ERROR_LIST:
                    existing_handler_methods[err_num] = class_member[1]

        yield_api_error_list = self.yield_api_error_list()

        for err_num in yield_api_error_list:
            if err_num not in existing_handler_methods:
                self.ERROR_CODE_HANDLER[err_num] = generic_handler_method
                continue

            self.ERROR_CODE_HANDLER[err_num] = existing_handler_methods[err_num] # noqa

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
                if err_num in self.API_ERROR_LIST:
                    existing_exceptions[err_num] = class_member[1]

        yield_api_error_list = self.yield_api_error_list()

        for err_num in yield_api_error_list:
            if err_num not in existing_exceptions:
                self.API_EXCEPTION_DICT[err_num] = exceptions.APIError
                continue

            self.API_EXCEPTION_DICT[err_num] = existing_exceptions[err_num]

    def yield_api_error_list(self):
        for err_num in self.API_ERROR_LIST:
            yield err_num
