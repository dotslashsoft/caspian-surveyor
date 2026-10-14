import pytest
import sqlite3
import dataclasses
from typing import Any
from caspian_surveyor.db.system_archive_reconstruction import *


class TestArchivedSystemQueries:
    def setup_method(self):
        self.connection_manager = ConnectionManager()
        self.conn = self.connection_manager.establish_db_connection()
        self.database_schema = self.connection_manager.database_schema
        self.database_file = self.connection_manager.database_file

    def teardown_method(self):
        self.conn.close()

    @pytest.fixture
    def db_connection(self, tmp_path):
        self.connection_manager.database_file = tmp_path / "test_archive.db"
        yield self.conn
        self.conn.close()

    def test_establish_db_connection(self, db_connection):
        assert isinstance(db_connection, sqlite3.Connection)
        assert db_connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0] == 1

    def test_original_payload(self):
        original_payload = load_current_system_record()
        assert original_payload is not None
        assert dataclasses.is_dataclass(original_payload)

    def test_reconstructed_payload(self):
        adapter = ArchivedSystemQueries()
        system_address = 38562352187

        reconstructed_payload = adapter.get_archived_system_info(self.conn, system_address)

        assert reconstructed_payload is not None
        assert reconstructed_payload.system.system_address == system_address

    def test_execute_query_statement(self):
        results_most_recent_body = execute_query_statement(self.conn, GET_MOST_RECENT_BODY)
        assert execute_query_statement(self.conn, GET_MOST_RECENT_BODY)
        assert results_most_recent_body is not None
        assert results_most_recent_body is not list[Any]