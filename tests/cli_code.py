    # def add(self, filename=None):
    #     try:
    #         username, password = self.user_manager.vpn_credentials
    #     except (
    #         exceptions.JSONAuthDataNoneError, exceptions.JSONAuthDataEmptyError
    #     ):
    #         print("[!] No stored session was found, try to login first.")
    #         sys.exit(1)

    #     try:
    #         self.connection_manager.add_connection(
    #             self.filename, username, password
    #         )
    #     except exceptions.ImportConnectionError as e:
    #         print(e)
    #         sys.exit(1)

    # def start(self):
    #     self.connection_manager.start_connection()

    # def remove(self):
    #     try:
    #         self.connection_manager.remove_connection()
    #     except exceptions.ConnectionNotFound as e:
    #         print("[!] {}".format(e))
    #         sys.exit(1)