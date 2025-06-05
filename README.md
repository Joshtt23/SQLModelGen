# SQLModelGen

## Usage & Development

### Installation (Development)

```bash
python -m venv .venv
.venv/Scripts/activate  # On Windows
# Or: source .venv/bin/activate  # On macOS/Linux
pip install -e .[dev]
```

### Running the CLI

```bash
sqlmodelgen generate --config config.yaml
sqlmodelgen inspect --config config.yaml
```

### Running Tests

```bash
pytest
```

- All tests are in the `tests/` directory.
- Coverage: `pytest --cov=src/sqlmodelgen`
- Linting: `flake8 src/ tests/`
- Type checking: `mypy src/ tests/`
- Formatting: `black src/ tests/`

---

SQLModelGen is a CLI tool that automatically generates [SQLModel](https://sqlmodel.tiangolo.com/) models (including enums) directly from a Postgres database via SQLAlchemy introspection.

## Features
- **Automatic model generation**: No manual schema files required
- **Configurable**: Exclusions, naming rules, overrides, and more
- **Postgres support**: Handles arrays, JSONB, enums, relationships, and more
- **Enum extraction**: Generates Python enums from Postgres types
- **Relationship inference**: Detects and generates foreign key relationships
- **CLI interface**: Built with [Typer](https://typer.tiangolo.com/)
- **Open-source ready**: Clean structure, MIT license

## Installation

```bash
pip install sqlmodelgen
```

## Usage

```bash
sqlmodelgen generate --config config.yaml
sqlmodelgen inspect --config config.yaml
```

See the documentation for configuration options and advanced usage.

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

## Configuration

Supports `.sqlmodelgen.yaml` or `.toml` config files with options for database URL, output directory, exclusions, enum output path, type overrides, and more.

## License

MIT

---

Developed by Finatic.dev 