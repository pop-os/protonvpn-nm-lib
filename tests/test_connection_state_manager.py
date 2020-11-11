import json
import os

import pytest

from common import PWD
from common import ConnectionStateManager
from common import exceptions

conn_state_filepath = os.path.join(PWD, "test_conn_state_manager.json")


class TestConnectionStateManager:
    csm = ConnectionStateManager()

    @classmethod
    def setup_class(cls):
        with open(conn_state_filepath, "w") as f:
            json.dump({
                "test_passed": True
            }, f)

    @classmethod
    def teardown_class(cls):
        try:
            os.remove(conn_state_filepath)
        except FileNotFoundError:
            pass

    def test_get_correct_filepath(self):
        with open(conn_state_filepath) as f:
            metadata = json.load(f)

        assert metadata["test_passed"] is True

    @pytest.mark.parametrize(
        "metadata_type, e",
        [
            ("random_metadata_type", exceptions.IllegalMetadataTypeError),
            ("", exceptions.IllegalMetadataTypeError),
            (False, exceptions.IllegalMetadataTypeError),
            ([], TypeError),
            ({}, TypeError)
        ]
    )
    def test_get_incorrect_metadata_type(self, metadata_type, e):
        with pytest.raises(e):
            self.csm.get_connection_metadata(metadata_type)

    def test_correct_save_servername(self):
        self.csm.save_servername("test_server#100")

    def test_correct_save_connected_time(self):
        self.csm.save_connected_time()
