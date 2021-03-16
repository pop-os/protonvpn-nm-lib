from protonvpn_nm_lib.core.environment import ExecutionEnvironment
from protonvpn_nm_lib.enums import ProtocolEnum

session = ExecutionEnvironment().api_session
#session.authenticate('username', "password")

fastest = session.servers.filter(lambda x: x.tier == 2).get_fastest_server()
configuration = fastest.get_random_physical_server().get_configuration(
    ProtocolEnum.UDP
)
with configuration as filename:
    print("Here we could import", filename)
    
print("Now the file is deleted")
print("Here's the configuration as string:")
print(configuration.generate())

print("")
print("You can play now:")
import IPython
IPython.embed()
