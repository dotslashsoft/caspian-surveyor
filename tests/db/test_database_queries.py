import pytest
import sqlite3

from caspian_surveyor.db.sql_statements import QUERY_ALL_BODIES, QUERY_ALL_SYSTEMS
from caspian_surveyor.db.system_archive_reconstruction import *
from tests.conftests import *

class TestDatabaseQueries:
    def setup_method(self):
        self.connection_manager = Connection().manager

    def test_establish_db_connection(self, temp_db):
        assert isinstance(temp_db, sqlite3.Connection)
        assert temp_db.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0] == 1

    def test_initialize_schema(self, temp_db):
        self.connection_manager.initialize_schema(temp_db)
        result = temp_db.execute(
            "SELECT name FROM sqlite_master WHERE name = 'systems'"
        ).fetchone()
        assert result is not None

    def test_query_all_systems(self, temp_db):
        results = execute_query_statement(temp_db, QUERY_ALL_SYSTEMS)
        assert isinstance(results, list)

    def test_query_all_bodies(self, temp_db):
        results = execute_query_statement(temp_db, QUERY_ALL_BODIES)
        assert isinstance(results, list)