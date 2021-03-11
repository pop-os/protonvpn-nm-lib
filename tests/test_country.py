# @pytest.mark.parametrize(
#         "cc,country",
#         [
#             ("BR", "Brazil"),
#             ("BS", "Bahamas"),
#             ("GR", "Greece"),
#             ("GQ", "Equatorial Guinea"),
#             ("GP", "Guadeloupe"),
#             ("JP", "Japan"),
#             ("GY", "Guyana"),
#         ]
#     )
#     def test_correct_country_name(self, cc, country):
#         assert self.server_man.extract_country_name(cc) == country

#     @pytest.mark.parametrize(
#         "cc,country",
#         [
#             ("BS", "Brazil"),
#             ("BR", "Bahamas"),
#             ("GQ", "Greece"),
#             ("GR", "Equatorial Guinea"),
#             ("JP", "Guadeloupe"),
#             ("GP", "Japan"),
#             ("Z", "Guyana"),
#             ("", "Guyana"),
#             (5, "Guyana"),
#         ]
#     )
#     def test_incorrect_extract_country_name(self, cc, country):
#         assert self.server_man.extract_country_name(cc) != country