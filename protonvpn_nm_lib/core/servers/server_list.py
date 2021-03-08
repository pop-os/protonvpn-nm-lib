from .logical_server import LogicalServer


class ServerList:

    def __init__(self, server_list_from_file):
        self.server_list = []
        for server in server_list_from_file["LogicalServers"]:
            self.server_list.append(LogicalServer(server))

    def filter_server_list(self):
        pass

    def serialize_server_list_to_dict(self):
        original_format = {"LogicalServers": []}

        for server in self.server_list:
            original_format["LogicalServers"].append(
                server.get_serialized_server()
            )

        return original_format
