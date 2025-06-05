# SQLModelGen

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/sqlmodelgen.svg)](https://pypi.org/project/sqlmodelgen/)

**SQLModelGen** is a CLI tool that automatically generates [SQLModel](https://sqlmodel.tiangolo.com/) models (including enums) directly from a Postgres database via SQLAlchemy introspection.

---

## Features
- 🚀 **Automatic model & enum generation** from your live Postgres database
- ⚙️ **Configurable**: exclusions, naming rules, type overrides, and more
- 🗄️ **Postgres support**: arrays, JSONB, enums, relationships, and more
- 🔗 **Relationship inference**: detects and generates foreign key relationships
- 🖥️ **CLI interface**: built with [Typer](https://typer.tiangolo.com/)
- 👐 **Open-source & commercial friendly**: MIT license, use for any purpose

---

## Installation

**From PyPI (recommended):**
```bash
pip install sqlmodelgen
```

**For local development:**
```bash
python -m venv .venv
.venv/Scripts/activate  # On Windows
# Or: source .venv/bin/activate  # On macOS/Linux
pip install -e .[dev]
```

---

## Usage

Place a config file named `sqlmodelgen.yaml`, `sqlmodelgen.yml`, or `sqlmodelgen.toml` in your project root, or specify one with `--config`.

```bash
# With default config file in current directory
sqlmodelgen generate
sqlmodelgen inspect

# Or specify a config file
sqlmodelgen generate --config path/to/config.yaml
sqlmodelgen inspect --config path/to/config.yaml
```

---

## Configuration

Supported config formats: **YAML** or **TOML**. Example:

```yaml
database_url: postgresql://user:pass@localhost:5432/mydb
output_dir: models
enum_output_path: enums
exclude_tables: [alembic_version]
exclude_columns: []
field_type_overrides: {}
relationship_mode: full
cleanup_old_files: true
```

See `example.sqlmodelgen.yaml` or `example.sqlmodelgen.toml` for all options.

---

## Example Output

```python
# models/user.py
from sqlmodel import SQLModel, Field, Relationship
from enums.user_status import UserStatus
from typing import Optional

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    status: UserStatus
    profile_id: Optional[int] = Field(default=None, foreign_key="profile.id")
    profile: Optional[Profile] = Relationship(back_populates="user")
```

---

## Development & Testing

- All tests are in the `tests/` directory.
- Run tests: `pytest`
- Coverage: `pytest --cov=src/sqlmodelgen`
- Linting: `flake8 src/ tests/`
- Type checking: `mypy src/ tests/`
- Formatting: `black src/ tests/`

---

## Contributing

We welcome contributions of all kinds! To get started:

1. **Fork the repository** and create your branch from `main`.
2. **Install dependencies**:
   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # On Windows
   # Or: source .venv/bin/activate  # On macOS/Linux
   pip install -e .[dev]
   ```
3. **Write tests** for your changes (see `tests/` directory).
4. **Lint and format your code**:
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/ tests/
   ```
5. **Open a pull request** with a clear description of your changes.

**Code style:**
- Follows [Black](https://black.readthedocs.io/en/stable/) formatting
- Linting with [Flake8](https://flake8.pycqa.org/)
- Type checking with [mypy](http://mypy-lang.org/)

---

## Community & Support

- **Issues:** [GitHub Issues](https://github.com/finaticdev/sqlmodelgen/issues)
- **Discussions:** [GitHub Discussions](https://github.com/finaticdev/sqlmodelgen/discussions)
- **Contact:** opensource@finatic.dev

If you have questions, ideas, or need help, open an issue or start a discussion!

---

## License

**MIT License** — free for personal, open-source, or commercial use. See [LICENSE](LICENSE).

---

Developed by [Finatic.dev](https://finatic.dev) — Contributions welcome! 