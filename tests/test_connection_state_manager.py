import json
import os

import pytest

from common import (PWD, ConnectionMetadataEnum, ConnectionStateManager,
                    MetadataEnum, exceptions)

conn_state_filepath = os.path.join(
    PWD, "test_conn_state_manager.json"
)
last_conn_state_filepath = os.path.join(
    PWD, "test_last_conn_state_manager.json"
)
remove_test_filepath = os.path.join(
    PWD, "remove_test.json"
)


class TestConnectionStateManager:
    csm = ConnectionStateManager()
    csm.METADATA_DICT = {
        MetadataEnum.CONNECTION: conn_state_filepath,
        MetadataEnum.LAST_CONNECTION: last_conn_state_filepath,
        MetadataEnum.SERVER_CACHE: remove_test_filepath
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

        with open(remove_test_filepath, "w") as f:
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

    @pytest.mark.parametrize(
        "metadata_type, output",
        [
            (MetadataEnum.CONNECTION, "conn_test"),
            (MetadataEnum.LAST_CONNECTION, "last_conn_test"),
        ]
    )
    def test_get_correct_metadata(self, metadata_type, output):
        metadata = self.csm.get_connection_metadata(metadata_type)
        assert output == metadata[ConnectionMetadataEnum.SERVER]

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

    def test_conn_save_servername(self):
        servername = "test_servername"
        self.csm.save_servername(servername)
        metadata = self.csm.get_connection_metadata(MetadataEnum.CONNECTION)
        assert servername == metadata[ConnectionMetadataEnum.SERVER]

    def test_last_conn_save_servername(self):
        servername = "test_last_conn_servername"
        self.csm.save_servername(servername)
        metadata = self.csm.get_connection_metadata(MetadataEnum.LAST_CONNECTION) # noqa
        assert servername == metadata[ConnectionMetadataEnum.SERVER]

    def test_conn_save_timestamp(self):
        self.csm.save_connected_time()
        metadata = self.csm.get_connection_metadata(MetadataEnum.CONNECTION)
        assert isinstance(
            int(metadata[ConnectionMetadataEnum.CONNECTED_TIME]),
            int
        )

    def test_conn_save_protocol(self):
        protocol = "test_protocol"
        self.csm.save_protocol(protocol)
        metadata = self.csm.get_connection_metadata(MetadataEnum.CONNECTION)
        assert protocol == metadata[ConnectionMetadataEnum.PROTOCOL]

    def test_conn_save_server_ip(self):
        ip = "192.168.1.192"
        self.csm.save_server_ip(ip)
        metadata = self.csm.get_connection_metadata(MetadataEnum.LAST_CONNECTION) # noqa
        assert ip == metadata["last_connect_ip"]

    def test_conn_get_server_ip(self):
        ip = "192.168.1.192"
        assert ip == self.csm.get_server_ip()

    def test_remove_metadata(self):
        self.csm.remove_connection_metadata(MetadataEnum.SERVER_CACHE)
        assert not os.path.isfile(remove_test_filepath)
