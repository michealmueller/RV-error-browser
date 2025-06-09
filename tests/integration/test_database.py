import pytest
import psycopg2
from ..utils import create_test_database, cleanup_test_database, get_test_connection
from ..db_config import DB_CONFIG, TEST_TABLE_SCHEMA, BUILDS_TABLE_SCHEMA, HISTORY_TABLE_SCHEMA

pytestmark = pytest.mark.skip(reason="Skipping database tests for now.")

@pytest.fixture(scope="session")
def test_db():
    """Create a test database and return connection info."""
    create_test_database()
    yield DB_CONFIG
    cleanup_test_database()

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
    """Test that all tables were created correctly."""
    cur = db_connection.cursor()
    
    # Test test_table
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'test_table'
    """)
    columns = cur.fetchall()
    
    expected_test_columns = {
        ('id', 'integer'),
        ('timestamp', 'timestamp without time zone'),
        ('level', 'character varying'),
        ('message', 'text')
    }
    assert set(columns) == expected_test_columns
    
    # Test builds table
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'builds'
    """)
    columns = cur.fetchall()
    
    expected_builds_columns = {
        ('id', 'integer'),
        ('build_id', 'character varying'),
        ('platform', 'character varying'),
        ('version', 'character varying'),
        ('status', 'character varying'),
        ('created_at', 'timestamp without time zone')
    }
    assert set(columns) == expected_builds_columns
    
    # Test history table
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'history'
    """)
    columns = cur.fetchall()
    
    expected_history_columns = {
        ('id', 'integer'),
        ('build_id', 'character varying'),
        ('platform', 'character varying'),
        ('version', 'character varying'),
        ('action', 'character varying'),
        ('status', 'character varying'),
        ('created_at', 'timestamp without time zone')
    }
    assert set(columns) == expected_history_columns
    
    cur.close()

def test_insert_and_query_test_table(db_connection):
    """Test inserting and querying data in test_table."""
    # Insert test data
    cur = db_connection.cursor()
    cur.execute("""
        INSERT INTO test_table (level, message)
        VALUES (%s, %s)
    """, ("INFO", "Test message"))
    db_connection.commit()
    
    # Query the data
    cur.execute("SELECT level, message FROM test_table")
    result = cur.fetchone()
    cur.close()
    
    assert result == ("INFO", "Test message")

def test_insert_and_query_builds_table(db_connection):
    """Test inserting and querying data in builds table."""
    # Insert test data
    cur = db_connection.cursor()
    cur.execute("""
        INSERT INTO builds (build_id, platform, version, status)
        VALUES (%s, %s, %s, %s)
    """, ("test-build-1", "android", "1.0.0", "available"))
    db_connection.commit()
    
    # Query the data
    cur.execute("SELECT build_id, platform, version, status FROM builds")
    result = cur.fetchone()
    cur.close()
    
    assert result == ("test-build-1", "android", "1.0.0", "available")

def test_insert_and_query_history_table(db_connection):
    """Test inserting and querying data in history table."""
    # Insert test data
    cur = db_connection.cursor()
    cur.execute("""
        INSERT INTO history (build_id, platform, version, action, status)
        VALUES (%s, %s, %s, %s, %s)
    """, ("test-build-1", "android", "1.0.0", "download", "success"))
    db_connection.commit()
    
    # Query the data
    cur.execute("SELECT build_id, platform, version, action, status FROM history")
    result = cur.fetchone()
    cur.close()
    
    assert result == ("test-build-1", "android", "1.0.0", "download", "success")

def test_error_handling(db_connection):
    """Test error handling for invalid queries."""
    cur = db_connection.cursor()
    with pytest.raises(psycopg2.Error):
        cur.execute("SELECT * FROM non_existent_table")
    cur.close() 