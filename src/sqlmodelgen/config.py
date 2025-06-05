import os
from typing import Any, Dict

try:
    import tomllib  # Python 3.11+
except ImportError:
    tomllib = None
import yaml


class ConfigError(Exception):
    pass


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    with open(
        path,
        "rb" if ext == ".toml" else "r",
        encoding=None if ext == ".toml" else "utf-8",
    ) as f:
        if ext in {".yaml", ".yml"}:
            config = yaml.safe_load(f)
        elif ext == ".toml":
            if not tomllib:
                raise ConfigError("tomllib is required for TOML config (Python 3.11+)")
            config = tomllib.load(f)
        else:
            raise ConfigError(f"Unsupported config file extension: {ext}")
    validate_config(config)
    return config


def validate_config(cfg: Dict[str, Any]) -> None:
    required = [
        "database_url",
        "output_dir",
        "enum_output_path",
    ]
    for key in required:
        if key not in cfg:
            raise ConfigError(f"Missing required config key: {key}")
    if not isinstance(cfg["database_url"], str):
        raise ConfigError("database_url must be a string")
    if not isinstance(cfg["output_dir"], str):
        raise ConfigError("output_dir must be a string")
    if not isinstance(cfg["enum_output_path"], str):
        raise ConfigError("enum_output_path must be a string")
    if "exclude_tables" in cfg and not isinstance(cfg["exclude_tables"], list):
        raise ConfigError("exclude_tables must be a list")
    if "exclude_columns" in cfg and not isinstance(cfg["exclude_columns"], list):
        raise ConfigError("exclude_columns must be a list")
    if "field_type_overrides" in cfg and not isinstance(
        cfg["field_type_overrides"], dict
    ):
        raise ConfigError("field_type_overrides must be a dict")
    if "relationship_mode" in cfg and cfg["relationship_mode"] not in (
        "minimal",
        "full",
    ):
        raise ConfigError("relationship_mode must be 'minimal' or 'full'")
