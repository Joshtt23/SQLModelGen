from typing import Any, Dict, List, Optional, Set
import os
from jinja2 import Environment, FileSystemLoader


class GenerationError(Exception):
    pass


# Simple SQL to Python type mapping for demonstration
SQL_TO_PYTHON_TYPE = {
    "INTEGER": "int",
    "BIGINT": "int",
    "SMALLINT": "int",
    "VARCHAR": "str",
    "TEXT": "str",
    "BOOLEAN": "bool",
    "TIMESTAMP": "datetime",
    "DATE": "date",
    "JSONB": "Json",
    "JSON": "Json",
    "UUID": "UUID",
    # Add more as needed
}


def _camel(name: str) -> str:
    return "".join(word.capitalize() for word in name.split("_"))


def _plural(name: str) -> str:
    if name.endswith("y"):
        return name[:-1] + "ies"
    elif name.endswith("s"):
        return name + "es"
    else:
        return name + "s"


class ModelGenerator:
    """
    Generates SQLModel models and Python enums from introspection data using Jinja2 templates.
    Handles idempotent file writing, cleanup, and preview mode.
    """

    def __init__(
        self,
        output_dir: str,
        enum_output_dir: str,
        template_dir: str,
        preview: bool = False,
    ) -> None:
        self.output_dir = output_dir
        self.enum_output_dir = enum_output_dir
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)
        self.preview = preview

    def _map_type(
        self,
        col: Dict[str, Any],
        enums: Dict[str, List[str]],
        type_overrides: Optional[Dict[str, str]] = None,
    ) -> str:
        # Config-based override
        if type_overrides and col["type"] in type_overrides:
            return type_overrides[col["type"]]
        # Enum support
        if col.get("enum_name"):
            return col["enum_name"]
        # Array support (Postgres arrays)
        col_type_str = str(col["type"])
        if col.get("is_array") or col_type_str.upper() == "ARRAY":
            element_type = col.get("element_type", "str")
            element_type_str = str(element_type)
            # If the element_type is a known enum, use it
            if element_type_str in enums:
                py_elem_type = element_type_str
            # If the element_type is a known SQL type, use the mapped Python type
            elif element_type_str.upper() in SQL_TO_PYTHON_TYPE:
                py_elem_type = SQL_TO_PYTHON_TYPE[element_type_str.upper()]
            else:
                py_elem_type = element_type_str.capitalize()
            return f"List[{py_elem_type}]"
        sql_type = col_type_str.upper()
        # If the type is a known enum, use it
        if col_type_str in enums:
            return col_type_str
        # If the type is a known SQL type, use the mapped Python type (capitalized)
        if sql_type in SQL_TO_PYTHON_TYPE:
            return SQL_TO_PYTHON_TYPE[sql_type]
        # Otherwise, capitalize the type name
        return col_type_str.capitalize()

    def _is_one_to_one(
        self, fk: Dict[str, Any], unique_constraints: List[List[str]]
    ) -> bool:
        # If the constrained column is unique, it's a one-to-one
        for uc in unique_constraints:
            if fk["constrained_columns"] == uc:
                return True
        return False

    def _is_association_table(
        self, table: str, columns: List[Dict[str, Any]], fks: List[Dict[str, Any]]
    ) -> bool:
        # Association table: only two FKs, both are PKs, and no other columns
        if len(fks) == 2 and len(columns) == 2:
            pk_cols = [
                c["name"]
                for c in columns
                if not c.get("nullable", True) and c.get("primary_key", False)
            ]
            fk_cols = [fk["constrained_columns"][0] for fk in fks]
            return set(pk_cols) == set(fk_cols)
        return False

    def build_relationship_map(
        self,
        all_tables: List[str],
        all_fks: Dict[str, List[Dict[str, Any]]],
        all_columns: Dict[str, List[Dict[str, Any]]],
        all_uniques: Optional[Dict[str, List[List[str]]]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build a map of table -> list of relationship dicts, including reverse relationships.
        Supports one-to-one and many-to-many.
        """
        rel_map: Dict[str, List[Dict[str, Any]]] = {t: [] for t in all_tables}
        all_uniques = all_uniques or {t: [] for t in all_tables}
        # Detect association tables for many-to-many
        association_tables = set()
        for table in all_tables:
            if self._is_association_table(
                table, all_columns[table], all_fks.get(table, [])
            ):
                association_tables.add(table)
        for table, fks in all_fks.items():
            for fk in fks:
                is_one_to_one = self._is_one_to_one(fk, all_uniques.get(table, []))
                # Forward relationship
                rel_map[table].append(
                    {
                        "direction": "forward",
                        "field_name": fk["constrained_columns"][0].replace("_id", ""),
                        "target_table": fk["referred_table"],
                        "back_populates": (
                            _plural(table) if not is_one_to_one else table
                        ),
                        "is_list": False if is_one_to_one else False,
                        "is_one_to_one": is_one_to_one,
                        "is_many_to_many": False,
                    }
                )
                # Reverse relationship
                rel_map[fk["referred_table"]].append(
                    {
                        "direction": "reverse",
                        "field_name": _plural(table) if not is_one_to_one else table,
                        "target_table": table,
                        "back_populates": fk["constrained_columns"][0].replace(
                            "_id", ""
                        ),
                        "is_list": not is_one_to_one,
                        "is_one_to_one": is_one_to_one,
                        "is_many_to_many": False,
                    }
                )
        # Many-to-many
        for assoc in association_tables:
            fks = all_fks[assoc]
            left, right = fks[0]["referred_table"], fks[1]["referred_table"]
            # Add List[Right] to Left
            rel_map[left].append(
                {
                    "direction": "m2m",
                    "field_name": _plural(right),
                    "target_table": right,
                    "back_populates": _plural(left),
                    "is_list": True,
                    "is_one_to_one": False,
                    "is_many_to_many": True,
                    "association_table": assoc,
                }
            )
            # Add List[Left] to Right
            rel_map[right].append(
                {
                    "direction": "m2m",
                    "field_name": _plural(left),
                    "target_table": left,
                    "back_populates": _plural(right),
                    "is_list": True,
                    "is_one_to_one": False,
                    "is_many_to_many": True,
                    "association_table": assoc,
                }
            )
        return rel_map

    def generate_model(
        self,
        table: Dict[str, Any],
        columns: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        enums: Dict[str, List[str]],
        type_overrides: Optional[Dict[str, str]] = None,
        rel_map: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> str:
        """
        Render a SQLModel model for a table using the model.jinja2 template.
        Returns the rendered code as a string.
        """
        fields = []
        extra_imports = set()
        for col in columns:
            py_type = self._map_type(col, enums, type_overrides)
            nullable = col.get("nullable", True)
            default = col.get("default")
            is_primary = col.get("primary_key", False) or col["name"] == "id"
            is_uuid = py_type == "UUID"
            is_array = (
                col.get("is_array") or str(col.get("type", "")).upper() == "ARRAY"
            )
            # Use None | Type for optionals (Python 3.10+)
            if nullable and not py_type.startswith("List["):
                field_type = f"None | {py_type}"
            else:
                field_type = py_type
            field_line = f"{col['name']}: {field_type}"
            field_args = []
            # UUID handling
            if is_uuid:
                extra_imports.add("from uuid import UUID, uuid4")
                extra_imports.add(
                    "from sqlalchemy.dialects.postgresql import UUID as PG_UUID"
                )
                if is_primary:
                    field_args.append("default_factory=uuid4")
                    field_args.append("primary_key=True")
                if not is_primary and not nullable:
                    field_args.append("...")
                field_args.append("sa_type=PG_UUID(as_uuid=True)")
            elif is_array:
                # Array handling: use List[Type] and sa_column=Column(ARRAY(String))
                extra_imports.add("from typing import List")
                extra_imports.add("from sqlalchemy import Column, String")
                extra_imports.add("from sqlalchemy.dialects.postgresql import ARRAY")
                element_type = col.get("element_type", "str")
                # Use String for str, otherwise fallback to element_type
                array_type = (
                    "String" if element_type in ("str", "String") else element_type
                )
                field_args.append(f"sa_column=Column(ARRAY({array_type}))")
            else:
                if py_type == "datetime":
                    extra_imports.add("from datetime import datetime")
                if py_type == "date":
                    extra_imports.add("from datetime import date")
                if py_type == "Json":
                    extra_imports.add("from pydantic import Json")
                    extra_imports.add(
                        "from sqlalchemy.dialects.postgresql import JSONB as PG_JSON"
                    )
                if py_type == "dict":
                    extra_imports.add("from typing import Any, Dict")
                if py_type in enums:
                    extra_imports.add(f"from enums.{py_type.lower()} import {py_type}")
                    extra_imports.add("from sqlalchemy import Enum as SAEnum")
                    field_args.append(
                        f'sa_type=SAEnum({py_type}, name="{py_type.lower()}")'
                    )
                if py_type.startswith("List["):
                    extra_imports.add("from typing import List")
                if not nullable:
                    if is_primary:
                        field_args.append("primary_key=True")
                    else:
                        field_args.append("...")
                elif default is not None:
                    field_args.append(f"default={default!r}")
            if field_args:
                field_line += f" = Field({', '.join(field_args)})"
            fields.append(field_line)
        rel_lines = []
        if rel_map:
            this_table = table["name"]
            for rel in rel_map.get(this_table, []):
                target = _camel(rel["target_table"])
                if rel["is_many_to_many"]:
                    rel_type = f"List[{target}]"
                    extra_imports.add("from typing import List")
                    rel_lines.append(
                        f"{rel['field_name']}: {rel_type} = Relationship(back_populates=\"{rel['back_populates']}\", link_model={_camel(rel['association_table'])})"
                    )
                elif rel["is_one_to_one"]:
                    rel_type = f"None | {target}"
                    rel_lines.append(
                        f"{rel['field_name']}: {rel_type} = Relationship(back_populates=\"{rel['back_populates']}\")"
                    )
                elif rel["is_list"]:
                    rel_type = f"List[{target}]"
                    extra_imports.add("from typing import List")
                    rel_lines.append(
                        f"{rel['field_name']}: {rel_type} = Relationship(back_populates=\"{rel['back_populates']}\")"
                    )
                else:
                    rel_type = f"None | {target}"
                    rel_lines.append(
                        f"{rel['field_name']}: {rel_type} = Relationship(back_populates=\"{rel['back_populates']}\")"
                    )
        else:
            for rel in relationships:
                target = rel["referred_table"].title().replace("_", "")
                rel_name = rel["constrained_columns"][0].replace("_id", "")
                rel_lines.append(
                    f"{rel_name}: None | {target} = Relationship(back_populates=\"{table['name']}\")"
                )
        template = self.env.get_template("model.jinja2")
        context = {
            "class_name": _camel(table["name"]),
            "fields": fields,
            "relationships": rel_lines,
            "extra_imports": sorted(extra_imports),
        }
        return template.render(**context)

    def generate_enum(self, enum_name: str, values: List[str]) -> str:
        """
        Render a Python Enum class using the enum.jinja2 template.
        Returns the rendered code as a string.
        """
        template = self.env.get_template("enum.jinja2")
        context = {
            "enum_name": enum_name,
            "values": values,
        }
        return template.render(**context)

    def write_model_file(
        self, class_name: str, code: str, written_files: Optional[Set[str]] = None
    ) -> None:
        """
        Write the generated model code to the output directory.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.abspath(
            os.path.join(self.output_dir, f"{class_name.lower()}.py")
        )
        if written_files is not None:
            written_files.add(path)
        if self.preview:
            print(f"[PREVIEW] Would write model: {path}\n{code}\n{'-'*40}")
            return
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = f.read()
            if existing == code:
                return  # Idempotent: do not rewrite
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

    def write_enum_file(
        self, enum_name: str, code: str, written_files: Optional[Set[str]] = None
    ) -> None:
        """
        Write the generated enum code to the enum output directory.
        """
        os.makedirs(self.enum_output_dir, exist_ok=True)
        path = os.path.abspath(
            os.path.join(self.enum_output_dir, f"{enum_name.lower()}.py")
        )
        if written_files is not None:
            written_files.add(path)
        if self.preview:
            print(f"[PREVIEW] Would write enum: {path}\n{code}\n{'-'*40}")
            return
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                existing = f.read()
            if existing == code:
                return
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)

    def cleanup_old_files(self, keep_files: Set[str], target_dir: str) -> None:
        for fname in os.listdir(target_dir):
            fpath = os.path.abspath(os.path.join(target_dir, fname))
            if fpath not in keep_files and fname.endswith(".py"):
                if self.preview:
                    print(f"[PREVIEW] Would delete: {fpath}")
                else:
                    os.remove(fpath)
