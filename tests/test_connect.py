    # @pytest.mark.parametrize(
    #     "servername",
    #     [
    #         "PT#5",
    #         "SE-PT#123",
    #         "CH#18-TOR",
    #         "US-CA#999",
    #         "CH-FI#8",
    #         "ch-fi#8",
    #     ]
    # )
    # def test_valid_servername(self, servername):
    #     resp = self.server_man.is_servername_valid(servername)
    #     assert resp is True

    # @pytest.mark.parametrize(
    #     "servername",
    #     [
    #         "_#1",
    #         "123#412",
    #         "#123",
    #         "test2#412",
    #         "CH#",
    #         "#",
    #         "5",
    #     ]
    # )
    # def test_invalid_servername(self, servername):
    #     resp = self.server_man.is_servername_valid(servername)
    #     assert resp is False

    # @pytest.mark.parametrize(
    #     "servername",
    #     [
    #         [], {}, 132
    #     ]
    # )
    # def test_more_incorrect_servernames(self, servername):
    #     with pytest.raises(TypeError):
    #         self.server_man.is_servername_valid(servername)