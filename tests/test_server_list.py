# class TestUnitServerManager:
#     server_man = ServerManager(um)
#     MOCKED_SESSION = ProtonSessionWrapper(
#         api_url="https://localhost",
#         user_manager=um
#     )

#     @classmethod
#     def setup_class(cls):
#         try:
#             os.mkdir(TEST_CACHED_SERVERFILE)
#         except FileExistsError:
#             shutil.rmtree(TEST_CACHED_SERVERFILE)
#             os.mkdir(TEST_CACHED_SERVERFILE)

#         um.session_data.store_data(
#             data=MOCK_SESSIONDATA,
#             keyring_username=TEST_KEYRING_SESSIONDATA,
#             keyring_service=TEST_KEYRING_SERVICE
#         )
#         um.session_data.store_data(
#             data=dict(
#                 VPN=dict(
#                     Name="test_username",
#                     Password="test_password",
#                     MaxTier="2",
#                 )
#             ),
#             keyring_username=TEST_KEYRING_USERDATA,
#             keyring_service=TEST_KEYRING_SERVICE,
#             store_user_data=True
#         )
#         um.session_data.store_data(
#             data={"test_proton_username": "test_server_man_user"},
#             keyring_username=TEST_KEYRING_PROTON_USER,
#             keyring_service=TEST_KEYRING_SERVICE,
#             store_user_data=False
#         )

#     @classmethod
#     def teardown_class(cls):
#         shutil.rmtree(TEST_CACHED_SERVERFILE)
#         um.session_data.delete_stored_data(TEST_KEYRING_PROTON_USER, TEST_KEYRING_SERVICE)
#         um.session_data.delete_stored_data(TEST_KEYRING_SESSIONDATA, TEST_KEYRING_SERVICE)
#         um.session_data.delete_stored_data(TEST_KEYRING_USERDATA, TEST_KEYRING_SERVICE)

#     @pytest.fixture
#     def mock_api_request(self):
#         mock_get_patcher = patch(
#             "protonvpn_nm_lib.core.proton_session_wrapper."
#             "Session.api_request"
#         )
#         yield mock_get_patcher.start()
#         mock_get_patcher.stop()

#     @pytest.mark.parametrize("servername", ["#", "", 5, None, {}, []])
#     def test_get_incorrect_get_pyshical_ip_list(
#         self, servername, mock_api_request
#     ):
#         mock_api_request.side_effect = [RAW_SERVER_LIST]
#         self.MOCKED_SESSION.cache_servers()
#         (
#             servers_list_object,
#             server,
#         ) = self.server_man.get_config_for_fastest_server()
#         with pytest.raises(IndexError):
#             servers_list_object.get_random_physical_server(server)

#     def test_get_correct_get_pyshical_ip_list(self, mock_api_request):
#         mock_api_request.side_effect = [RAW_SERVER_LIST]
#         (
#             servername,
#             server_feature,
#             filtered_servers,
#             servers
#         ) = self.server_man.get_config_for_specific_server(
#             servername=TestServernameEnum.TEST_5.value
#         )
#         servers = self.server_man.get_physical_server_list(
#             servername, SERVERS, filtered_servers
#         )
#         assert servers[0]["Domain"] == "pt-89.webtest.com"

#     def test_get_existing_label(self, mock_api_request):
#         mock_api_request.side_effect = [RAW_SERVER_LIST]
#         (
#             servername,
#             server_feature,
#             filtered_servers,
#             servers
#         ) = self.server_man.get_config_for_specific_server(
#             servername=TestServernameEnum.TEST_5.value
#         )
#         servers = self.server_man.get_physical_server_list(
#             servername, servers, filtered_servers
#         )

#         server = self.server_man.get_random_physical_server(servers)
#         label = self.server_man.get_server_label(server)
#         assert label == "TestLabel"

#     def test_get_missing_label(self, mock_api_request):
#         mock_api_request.side_effect = [RAW_SERVER_LIST]
#         (
#             servername,
#             server_feature,
#             filtered_servers,
#             servers
#         ) = self.server_man.get_config_for_specific_server(
#             servername=TestServernameEnum.TEST_6.value
#         )
#         servers = self.server_man.get_physical_server_list(
#             servername, servers, filtered_servers
#         )

#         server = self.server_man.get_random_physical_server(servers)
#         label = self.server_man.get_server_label(server)
#         assert label is None

#     def test_get_nonexisting_label(self, mock_api_request):
#         mock_api_request.side_effect = [RAW_SERVER_LIST]
#         (
#             servername,
#             server_feature,
#             filtered_servers,
#             servers
#         ) = self.server_man.get_config_for_specific_server(
#             servername=TestServernameEnum.TEST_6.value
#         )
#         servers = self.server_man.get_physical_server_list(
#             servername, servers, filtered_servers
#         )

#         server = self.server_man.get_random_physical_server(servers)
#         label = self.server_man.get_server_label(server)
#         assert label is None

#     def test_get_server_IP(self, mock_api_request):
#         mock_api_request.side_effect = [RAW_SERVER_LIST]
#         (
#             servername,
#             server_feature,
#             filtered_servers,
#             servers
#         ) = self.server_man.get_config_for_specific_server(
#             servername=TestServernameEnum.TEST_6.value
#         )
#         servers = self.server_man.get_physical_server_list(
#             servername, servers, filtered_servers
#         )

#         server = self.server_man.get_random_physical_server(servers)
#         ips = self.server_man.get_server_entry_exit_ip(server)
#         assert ips == ("255.211.255.0", "255.211.255.0")

#     @pytest.fixture
#     def empty_server_pool(self):
#         server_pool = []
#         return server_pool

#     @pytest.fixture
#     def full_server_pool(self):
#         feature = 0
#         server_pool = [s for s in SERVERS if s["Features"] == feature]
#         return server_pool

#     def test_get_fastest_server_empty_pool(self, empty_server_pool):
#         with pytest.raises(IndexError):
#             self.server_man.get_fastest_server(empty_server_pool)

#     def test_get_fastest_server_full_pool(self, full_server_pool):
#         self.server_man.get_fastest_server(full_server_pool)