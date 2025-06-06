import os
import yaml
import toml
from typing import Any, Dict


class ConfigError(Exception):
    pass


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")
    if path.endswith(".yaml") or path.endswith(".yml"):
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    elif path.endswith(".toml"):
        with open(path, "r", encoding="utf-8") as f:
            cfg = toml.load(f)
    else:
        raise ConfigError("Config file must be .yaml, .yml, or .toml")
    return apply_config_defaults(cfg)


def apply_config_defaults(cfg: Dict[str, Any]) -> Dict[str, Any]:
    # Backward compatibility for old keys
    output = cfg.get("output", {})
    # If old keys exist, use them unless new output section is present
    if not output:
        output = {}
        if "output_dir" in cfg:
            output["models"] = cfg["output_dir"]
        if "enum_output_path" in cfg:
            output["enums"] = cfg["enum_output_path"]
    # Set sensible defaults
    output.setdefault("models", "models.py")
    output.setdefault("enums", "enums.py")
    output.setdefault("split_models", False)
    output.setdefault("split_enums", False)
    cfg["output"] = output
    return cfg


def validate_config(cfg: Dict[str, Any]) -> None:
    if "database_url" not in cfg:
        raise ConfigError("Missing required config key: database_url")
    if not isinstance(cfg["database_url"], str):
        raise ConfigError("database_url must be a string")
    if "output" in cfg:
        output = cfg["output"]
        if not isinstance(output.get("models", ""), str):
            raise ConfigError("output.models must be a string (file or directory path)")
        if not isinstance(output.get("enums", ""), str):
            raise ConfigError("output.enums must be a string (file or directory path)")
        if not isinstance(output.get("split_models", False), bool):
            raise ConfigError("output.split_models must be a boolean")
        if not isinstance(output.get("split_enums", False), bool):
            raise ConfigError("output.split_enums must be a boolean")
    if "relationship_mode" in cfg and cfg["relationship_mode"] not in (
        "minimal",
        "full",
    ):
        raise ConfigError("relationship_mode must be 'minimal' or 'full'")
