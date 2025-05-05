import os
import pytest
from datetime import datetime

@pytest.mark.unit
def test_format_log_message():
    # Example log message formatter
    def format_log(msg: str, ts: datetime) -> str:
        return f'[{ts.strftime("%H:%M:%S")}] {msg}'
    now = datetime(2024, 1, 1, 12, 34, 56)
    assert format_log("Hello", now) == "[12:34:56] Hello"

@pytest.mark.unit
def test_parse_env_var():
    os.environ['TEST_ENV'] = 'foobar'
    def get_env(name: str, default: str = "") -> str:
        return os.getenv(name, default)
    assert get_env('TEST_ENV') == 'foobar'
    assert get_env('NOT_SET', 'default') == 'default'

@pytest.mark.unit
def test_build_db_conn_string():
    def build_conn(host: str, port: int, db: str, user: str) -> str:
        return f"host={host} port={port} dbname={db} user={user}"
    assert build_conn('localhost', 5432, 'mydb', 'user') == "host=localhost port=5432 dbname=mydb user=user" 