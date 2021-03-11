from protonvpn_nm_lib.client import Client
from protonvpn_nm_lib.enums import ConnectionTypeEnum

client = Client()
client.setup_connection(
    ConnectionTypeEnum.SERVERNAME,
    "CH#20"
)
# client.connect()

# client.login("calexandru2018@pm.me", "ProtonCheltuitor56")