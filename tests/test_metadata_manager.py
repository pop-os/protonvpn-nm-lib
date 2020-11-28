import json
import os

import pytest

from common import (PWD, MetadataActionEnum, MetadataEnum, MetadataManager,
                    exceptions)

conn_state_filepath = os.path.join(
    PWD, "test_metadata_manager.json"
)
last_conn_state_filepath = os.path.join(
    PWD, "test_last_metadata_manager.json"
)
test_create_filepath = os.path.join(
    PWD, "test_create_metadata_manager.json"
)


class TestMetadataManager():
    mm = MetadataManager()
    mm.METADATA_DICT = {
        MetadataEnum.CONNECTION: conn_state_filepath,
        MetadataEnum.LAST_CONNECTION: last_conn_state_filepath,
        MetadataEnum.SERVER_CACHE: test_create_filepath
    }

    @classmethod
    def setup_class(cls):
        with open(conn_state_filepath, "w") as f:
            json.dump({
                "connected_server": "conn_test",
                "connected_protocol": "tcp",
                "connected_time": 0000000
            }, f)

        with open(last_conn_state_filepath, "w") as f:
            json.dump({
                "connected_server": "last_conn_test",
                "last_connect_ip": "192.168.0.1"
            }, f)

    @classmethod
    def teardown_class(cls):
        try:
            os.remove(conn_state_filepath)
        except FileNotFoundError:
            pass

        try:
            os.remove(last_conn_state_filepath)
        except FileNotFoundError:
            pass

    def test_correct_manage_create_metadata(self):
        self.mm.manage_metadata(
            MetadataActionEnum.WRITE, MetadataEnum.SERVER_CACHE,
            {"test_file": "testing"}
        )
        assert "testing" == self.mm.manage_metadata(
            MetadataActionEnum.GET, MetadataEnum.SERVER_CACHE
        )["test_file"]

    @pytest.mark.parametrize(
        "metadata_action, exception",
        [
            (
                "MetadataEnum.SERVER_CACHE",
                exceptions.IllegalMetadataActionError
            ),
            (
                "",
                exceptions.IllegalMetadataActionError
            ),
            (
                2017,
                exceptions.IllegalMetadataActionError
            ),
        ]
    )
    def test_incorrect_manage_metadata_action(self, metadata_action, exception): # noqa
        with pytest.raises(exception):
            self.mm.manage_metadata(
                metadata_action, MetadataEnum.SERVER_CACHE,
                {"test_file": "testing"}
            )

    def test_correct_manage_delete_metadata(self):
        self.mm.manage_metadata(MetadataActionEnum.REMOVE, MetadataEnum.SERVER_CACHE) # noqa
        assert not os.path.isfile(test_create_filepath)

    @pytest.mark.parametrize(
        "metadata_type",
        [
            MetadataEnum.CONNECTION, MetadataEnum.LAST_CONNECTION,
            MetadataEnum.SERVER_CACHE
        ]
    )
    def test_check_correct_metadata_type(self, metadata_type):
        self.mm.check_metadata_type(metadata_type)
