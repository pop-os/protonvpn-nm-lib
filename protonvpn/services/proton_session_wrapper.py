from proton.api import ProtonError, Session
from ..logger import logger
from .. import exceptions


class ProtonSessionWrapper(Session):
    session = False

    def __init__(
        self, api_url, appversion,
        user_agent, TLSPinning=True
    ):
        super().__init__(
            api_url, appversion, user_agent, TLSPinning
        )

    def api_call(
        self, endpoint, jsondata=None,
        additional_headers=None, method=None
    ):
        # try:
        if not self.session:
            return self.api_request(
                endpoint, jsondata, additional_headers, method
            )
        else:
            return self.session.api_request(
                endpoint, jsondata, additional_headers, method
            )
        # except ProtonError as e:
        #     if e.code == 401:
        #         self.handle_401()

    def authenticate_wrapper(self, username, password):
        # try:
        self.authenticate(username, password)
        # except ProtonError as e:
        #     logger.exception("[!] API ProtonError: {}".format(e))
        #     if e.code == 8002:
        #         raise exceptions.IncorrectCredentialsError(e)
        #     else:
        #         raise exceptions.APIAuthenticationError(e)

    @staticmethod
    def load_wrapper(dump, TLSPinning=True):
        api_url = dump['api_url']
        appversion = dump['appversion']
        user_agent = dump['User-Agent']
        wrapper_session = ProtonSessionWrapper(
            api_url, appversion, user_agent, TLSPinning=TLSPinning
        )
        wrapper_session.session = wrapper_session.load(dump, TLSPinning=True)
        return wrapper_session

    def handle_401(self):
        print("Handle 401")
        # self.refresh()
