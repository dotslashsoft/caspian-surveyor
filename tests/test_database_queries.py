import pytest
import sqlite3

from caspian_surveyor.db.system_archive_reconstruction import *


class TestDatabaseQueries:

    def setup_method(self):
        self.connection_manager = Connection().manager
        self.conn = self.connection_manager.establish_db_connection()

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


    def test_initialize_schema(self, db_connection):
        self.connection_manager.initialize_schema(db_connection)
        result = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'systems'"
        ).fetchone()
        assert result is not None


    def test_query_all_systems(self):
        results = execute_query_statement(self.conn, QUERY_ALL_SYSTEMS)
        assert isinstance(results, list)


    def test_query_all_bodies(self):
        results = execute_query_statement(self.conn, QUERY_ALL_BODIES)
        assert isinstance(results, list)