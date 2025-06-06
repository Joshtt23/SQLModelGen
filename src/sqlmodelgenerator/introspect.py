from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, inspect, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text


class IntrospectionError(Exception):
    pass


class Introspector:
    """
    Handles database introspection for SQLModelGenerator.
    Connects to a Postgres database and extracts tables, columns, enums, and relationships.
    """

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[Engine] = None
        self.inspector: Optional[Inspector] = None
        self.metadata = MetaData()

    def connect(self) -> None:
        try:
            self.engine = create_engine(self.database_url)
            self.inspector = inspect(self.engine)
        except SQLAlchemyError as e:
            raise IntrospectionError(f"Failed to connect to database: {e}")

    def get_tables(self) -> List[str]:
        if not self.inspector:
            self.connect()
        return self.inspector.get_table_names(schema="public")

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        if not self.inspector:
            self.connect()
        return self.inspector.get_columns(table_name, schema="public")

    def get_foreign_keys(self, table_name: str) -> List[Dict[str, Any]]:
        if not self.inspector:
            self.connect()
        return self.inspector.get_foreign_keys(table_name, schema="public")

    def get_enums(self) -> Dict[str, List[str]]:
        """
        Returns a dict of enum name -> list of values.
        """
        if not self.engine:
            self.connect()
        sql = text(
            """
            SELECT t.typname AS enum_name, e.enumlabel AS enum_value
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            ORDER BY t.typname, e.enumsortorder;
        """
        )
        enums: Dict[str, List[str]] = {}
        with self.engine.connect() as conn:
            result = conn.execute(sql)
            for row in result:
                enums.setdefault(row.enum_name, []).append(row.enum_value)
        return enums

    def get_relationships(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Returns a list of relationships (foreign keys) for the given table.
        """
        return self.get_foreign_keys(table_name)
