import psycopg2
import pytest

from tests.db_config import DB_CONFIG
from utils import create_test_database, drop_test_database, get_test_connection


@pytest.fixture(scope="session")
def test_db():
    """Create a test database and return connection info."""
    create_test_database()
    yield DB_CONFIG
    drop_test_database()


@pytest.fixture
def db_connection(test_db):
    """Create a connection to the test database."""
    conn = get_test_connection()
    yield conn
    conn.close()


def test_database_connection(db_connection):
    """Test that we can connect to the database."""
    assert db_connection.status == 1  # Connection is open


def test_table_creation(db_connection):
    """Test that the test table was created correctly."""
    cur = db_connection.cursor()
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'test_table'
    """
    )
    columns = cur.fetchall()
    cur.close()

    expected_columns = {
        ("id", "integer"),
        ("timestamp", "timestamp without time zone"),
        ("level", "character varying"),
        ("message", "text"),
    }
    assert set(columns) == expected_columns


def test_insert_and_query(db_connection):
    """Test inserting and querying data."""
    # Insert test data
    cur = db_connection.cursor()
    cur.execute(
        """
        INSERT INTO test_table (level, message)
        VALUES (%s, %s)
    """,
        ("INFO", "Test message"),
    )
    db_connection.commit()

    # Query the data
    cur.execute("SELECT level, message FROM test_table")
    result = cur.fetchone()
    cur.close()

    assert result == ("INFO", "Test message")


def test_error_handling(db_connection):
    """Test error handling for invalid queries."""
    cur = db_connection.cursor()
    with pytest.raises(psycopg2.Error):
        cur.execute("SELECT * FROM non_existent_table")
    cur.close()
