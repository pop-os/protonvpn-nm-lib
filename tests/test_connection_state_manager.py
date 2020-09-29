import json
import os

import pytest

from common import PWD, ConnectionStateManager

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
        "filepath, e",
        [
            ("./some/incorrect/path.json", FileNotFoundError),
            ("", FileNotFoundError),
            (False, json.decoder.JSONDecodeError),
            ([], TypeError),
            ({}, TypeError)
        ]
    )
    def test_get_incorrect_filepath(self, filepath, e):
        self.csm.FILEPATH = filepath
        with pytest.raises(e):
            self.csm.get_connection_metadata()

    def test_correct_save_servername(self):
        self.csm.FILEPATH = conn_state_filepath
        self.csm.save_servername("test_server#100")

    def test_correct_save_connected_time(self):
        self.csm.FILEPATH = conn_state_filepath
        self.csm.save_connected_time()

    def test_remove_correct_connection_metadata(self):
        self.csm.FILEPATH = conn_state_filepath
        self.csm.remove_connection_metadata()

    def test_remove_incorrect_connection_metadata(self):
        self.csm.FILEPATH = "missing/path/file.json"
        with pytest.raises(FileNotFoundError):
            self.csm.remove_connection_metadata()
