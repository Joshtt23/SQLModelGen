import typer
from .config import load_config, ConfigError
from .introspect import Introspector, IntrospectionError
from .generate import ModelGenerator, GenerationError
import os
import sys
from rich.console import Console
from rich.table import Table

__version__ = "0.1.0"

app = typer.Typer(
    help="SQLModelGen: Generate SQLModel models from a Postgres database."
)
console = Console()


@app.command()
def version() -> None:
    """Show the SQLModelGen version."""
    console.print(f"SQLModelGen version {__version__}")


@app.command()
def generate(
    config: str = typer.Option(
        None,
        help="Path to config file. If not provided, will look for sqlmodelgen.yaml/yml/toml in the current directory.",
    ),
    preview: bool = typer.Option(False, help="Preview changes without writing files."),
) -> None:
    """Generate SQLModel models from the database."""
    try:
        if config is None:
            # Look for default config files in the current working directory
            for fname in ["sqlmodelgen.yaml", "sqlmodelgen.yml", "sqlmodelgen.toml"]:
                if os.path.exists(fname):
                    config = fname
                    break
            else:
                console.print(
                    "[red]No config file provided and no default config found in the current directory.[/red]"
                )
                sys.exit(1)
        cfg = load_config(config)
        introspector = Introspector(cfg["database_url"])
        tables = introspector.get_tables()
        enums = introspector.get_enums()
        output_dir = cfg.get("output_dir", "models")
        enum_output_dir = cfg.get("enum_output_path", "enums")
        type_overrides = cfg.get("field_type_overrides", {})
        exclude_tables = set(cfg.get("exclude_tables", []))
        exclude_columns = set(cfg.get("exclude_columns", []))
        relationship_mode = cfg.get("relationship_mode", "full")
        cleanup = cfg.get("cleanup_old_files", True)
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        generator = ModelGenerator(
            output_dir, enum_output_dir, template_dir, preview=preview
        )
        tables = [t for t in tables if t not in exclude_tables]
        written_model_files: set[str] = set()
        written_enum_files: set[str] = set()
        skipped_models = 0
        skipped_enums = 0
        deleted_files = []
        if preview:
            console.print(
                "[yellow][PREVIEW][/yellow] No files will be written or deleted."
            )
        if not tables:
            console.print("[yellow]No tables found to generate models for.[/yellow]")
        if not enums:
            console.print("[yellow]No enums found to generate.[/yellow]")
        # Generate enums first
        for enum_name, values in enums.items():
            code = generator.generate_enum(enum_name.title().replace("_", ""), values)
            path = os.path.join(enum_output_dir, f"{enum_name.lower()}.py")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    if f.read() == code:
                        skipped_enums += 1
                        continue
            generator.write_enum_file(
                enum_name.title().replace("_", ""), code, written_enum_files
            )
        # Prepare for relationship map if full mode
        all_fks = {t: introspector.get_foreign_keys(t) for t in tables}
        all_columns = {t: introspector.get_columns(t) for t in tables}
        rel_map = None
        if relationship_mode == "full":
            rel_map = generator.build_relationship_map(tables, all_fks, all_columns)
        # Generate models
        for table in tables:
            columns = [
                c
                for c in introspector.get_columns(table)
                if c["name"] not in exclude_columns
            ]
            relationships = introspector.get_foreign_keys(table)
            code = generator.generate_model(
                {"name": table},
                columns,
                relationships,
                enums,
                type_overrides,
                rel_map=rel_map if relationship_mode == "full" else None,
            )
            path = os.path.join(output_dir, f"{table.lower()}.py")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    if f.read() == code:
                        skipped_models += 1
                        continue
            generator.write_model_file(
                table.title().replace("_", ""), code, written_model_files
            )
        # Cleanup old files
        if cleanup:
            for fname in os.listdir(output_dir):
                fpath = os.path.join(output_dir, fname)
                if fpath not in written_model_files and fname.endswith(".py"):
                    deleted_files.append(fpath)
            for fname in os.listdir(enum_output_dir):
                fpath = os.path.join(enum_output_dir, fname)
                if fpath not in written_enum_files and fname.endswith(".py"):
                    deleted_files.append(fpath)
            generator.cleanup_old_files(written_model_files, output_dir)
            generator.cleanup_old_files(written_enum_files, enum_output_dir)
        # Print summary
        console.print(f"[green]Model and enum generation complete![/green]")
        console.print(
            f"[bold]Models written:[/bold] {len(written_model_files)} | "
            f"[bold]skipped:[/bold] {skipped_models}"
        )
        console.print(
            f"[bold]Enums written:[/bold] {len(written_enum_files)} | "
            f"[bold]skipped:[/bold] {skipped_enums}"
        )
        if deleted_files:
            console.print(f"[red]Deleted files:[/red] {', '.join(deleted_files)}")
    except (ConfigError, IntrospectionError, GenerationError) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def inspect(
    config: str = typer.Option(
        None,
        help="Path to config file. If not provided, will look for sqlmodelgen.yaml/yml/toml in the current directory.",
    )
) -> None:
    """Inspect the database schema and output a preview."""
    try:
        if config is None:
            for fname in ["sqlmodelgen.yaml", "sqlmodelgen.yml", "sqlmodelgen.toml"]:
                if os.path.exists(fname):
                    config = fname
                    break
            else:
                console.print(
                    "[red]No config file provided and no default config found in the current directory.[/red]"
                )
                sys.exit(1)
        cfg = load_config(config)
        introspector = Introspector(cfg["database_url"])
        tables = introspector.get_tables()
        enums = introspector.get_enums()
        exclude_tables = set(cfg.get("exclude_tables", []))
        exclude_columns = set(cfg.get("exclude_columns", []))
        tables = [t for t in tables if t not in exclude_tables]
        console.print("[bold]Tables:[/bold]")
        table = Table("Table Name", "Columns", "Foreign Keys")
        for t in tables:
            columns = [
                c
                for c in introspector.get_columns(t)
                if c["name"] not in exclude_columns
            ]
            col_names = ", ".join([c["name"] for c in columns])
            fks = introspector.get_foreign_keys(t)
            fk_str = (
                ", ".join(
                    [
                        f"{fk['constrained_columns'][0]}→{fk['referred_table']}.{fk['referred_columns'][0]}"
                        for fk in fks
                    ]
                )
                if fks
                else ""
            )
            table.add_row(t, col_names, fk_str)
        console.print(table)
        if enums:
            console.print("\n[bold]Enums:[/bold]")
            enum_table = Table("Enum Name", "Values")
            for name, values in enums.items():
                enum_table.add_row(name, ", ".join(values))
            console.print(enum_table)
    except (ConfigError, IntrospectionError) as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
