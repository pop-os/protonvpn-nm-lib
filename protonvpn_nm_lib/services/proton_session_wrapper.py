from proton.api import ProtonError, Session
from ..logger import logger
from .. import exceptions
import inspect


class ProtonSessionWrapper():
    """Proton-client wrapper for improved error handling."""
    proton_session = False
    API_ERROR_LIST = [
        400, 401, 403, 404, 409,
        422, 429, 500, 501, 503,
    ]
    API_EXCEPTION_DICT = {}
    ERROR_CODE_HANDLER = {}

    def __init__(
        self, **kwargs
    ):
        self.setup_error_handling("handle_trivial_status")
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
            logger.exception("[!] Unknown exception: {}".format(e))
            raise Exception("Unknown error: {}".format(e))

        if not error:
            return api_response

        try:
            result = self.ERROR_CODE_HANDLER[error.code](
                error, args, **api_kwargs
            )
        except KeyError as e:
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
        self.proton_session.authenticate(username, password)

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
                error, None, None
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

    def handle_trivial_status(self, error):
        logger.info("Catched {} error".format(error.code))
        raise self.API_EXCEPTION_DICT[error.code](error.Error)

    def handle_401(self, error, *args, **kwargs):
        """Handles access token expiration."""
        logger.info("Catched 401 error")
        logger.info("Refreshing session data")
        self.proton_session.refresh()
        # Store session data
        logger.info("Storing new session data")
        self.user_manager.store_data(
            self.proton_session.dump(),
            self.user_manager.keyring_sessiondata,
            self.user_manager.keyring_service
        )
        logger.info("Calling api_request")
        return self.api_request(*args, **kwargs)

    def handle_403(self, error, *args, **kwargs):
        logger.info("Catched 403 error")
        raise exceptions.API403Error(error)

    def handle_429(self, error, *args, **kwargs):
        logger.info("Catched 429 error")
        raise exceptions.API429Error(error)

    def handle_503(self, error, *args, **kwargs):
        logger.info("Catched 504 error")
        raise exceptions.API503Error(error)

    def setup_error_handling(self, generic_handler_method_name):
        """Setup automatic error handling.

        All API handler methods should start with "handle_" and
        then the number of the HTTP status that is to be handled.
        The rest is taked care of by the code.

        Args:
            generic_handler_method_name (string):
                name of the generic handler method
        """
        existing_handler_methods = {}
        generic_handler_method = None
        for class_member in inspect.getmembers(self):
            if "handle_" in class_member[0]:
                _, err_num, *_ = class_member[0].split("_")
                try:
                    err_num = int(err_num)
                except ValueError:
                    if generic_handler_method_name == class_member[0]:
                        generic_handler_method = class_member[1]
                else:
                    if err_num in self.API_ERROR_LIST:
                        existing_handler_methods[err_num] = class_member[1]

        for err_num in self.API_ERROR_LIST:
            if err_num not in existing_handler_methods:
                self.ERROR_CODE_HANDLER[err_num] = generic_handler_method
            else:
                self.ERROR_CODE_HANDLER[err_num] = existing_handler_methods[err_num] # noqa

    def setup_exception_handling(self):
        """Setup automatic exception handling

        This will search for exception that start with "API"
        """
        import re
        for class_member in inspect.getmembers(exceptions):
            if "API" in class_member[0]:
                excp_name = class_member[0]
                re_api_status_code = re.compile(
                    r"^([A-Za-z]+)(\d+)([A-Za-z]+)$"
                )
                result = re_api_status_code.search(excp_name)
                if not result:
                    continue

                err_num = result.groups()[1]

                if err_num in self.API_ERROR_LIST:
                    self.API_EXCEPTION_DICT[err_num] = class_member[1]
                else:
                    self.API_EXCEPTION_DICT[err_num] \
                        = exceptions.UnhandledAPIError
