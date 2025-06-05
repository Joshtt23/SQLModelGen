from unittest.mock import MagicMock, patch
from sqlmodelgen.introspect import Introspector


@patch("sqlmodelgen.introspect.create_engine")
@patch("sqlmodelgen.introspect.inspect")
def test_get_tables_and_columns(mock_inspect, mock_create_engine):
    mock_engine = MagicMock()
    mock_inspector = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_inspect.return_value = mock_inspector
    mock_inspector.get_table_names.return_value = ["user", "profile"]
    mock_inspector.get_columns.side_effect = lambda table, schema=None: [
        {"name": "id", "type": "INTEGER", "nullable": False},
        {"name": "name", "type": "VARCHAR", "nullable": True},
    ]
    introspector = Introspector("postgresql://user:pass@localhost/db")
    tables = introspector.get_tables()
    assert tables == ["user", "profile"]
    columns = introspector.get_columns("user")
    assert columns[0]["name"] == "id"
    assert columns[1]["name"] == "name"


@patch("sqlmodelgen.introspect.create_engine")
@patch("sqlmodelgen.introspect.inspect")
def test_get_foreign_keys(mock_inspect, mock_create_engine):
    mock_engine = MagicMock()
    mock_inspector = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_inspect.return_value = mock_inspector
    mock_inspector.get_foreign_keys.return_value = [
        {
            "constrained_columns": ["profile_id"],
            "referred_table": "profile",
            "referred_columns": ["id"],
        }
    ]
    introspector = Introspector("postgresql://user:pass@localhost/db")
    fks = introspector.get_foreign_keys("user")
    assert fks[0]["constrained_columns"] == ["profile_id"]
    assert fks[0]["referred_table"] == "profile"


@patch("sqlmodelgen.introspect.create_engine")
@patch("sqlmodelgen.introspect.inspect")
def test_get_enums(mock_inspect, mock_create_engine):
    mock_engine = MagicMock()
    mock_create_engine.return_value = mock_engine
    mock_conn = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.execute.return_value = [
        MagicMock(enum_name="user_status", enum_value="active"),
        MagicMock(enum_name="user_status", enum_value="inactive"),
        MagicMock(enum_name="role", enum_value="admin"),
    ]
    mock_inspect.return_value = MagicMock()
    from sqlmodelgen.introspect import Introspector

    introspector = Introspector("postgresql://user:pass@localhost/db")
    enums = introspector.get_enums()
    assert enums["user_status"] == ["active", "inactive"]
    assert enums["role"] == ["admin"]
