import tempfile
import yaml
import pytest
from sqlmodelgen.config import load_config, ConfigError, validate_config


def test_load_yaml_config():
    config_data = {
        "database_url": "postgresql://user:pass@localhost/db",
        "output_dir": "models",
        "exclude_tables": [],
        "exclude_columns": [],
        "enum_output_path": "enums",
        "field_type_overrides": {},
        "relationship_mode": "minimal",
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        f.flush()
        loaded = load_config(f.name)
    assert loaded["database_url"] == config_data["database_url"]
    assert loaded["output_dir"] == config_data["output_dir"]


def test_config_missing_required_key():
    cfg = {
        "output_dir": "models",
        "enum_output_path": "enums",
    }
    with pytest.raises(ConfigError) as e:
        validate_config(cfg)
    assert "Missing required config key: database_url" in str(e.value)


def test_config_wrong_type():
    cfg = {
        "database_url": 123,
        "output_dir": "models",
        "enum_output_path": "enums",
    }
    with pytest.raises(ConfigError) as e:
        validate_config(cfg)
    assert "database_url must be a string" in str(e.value)


def test_config_invalid_relationship_mode():
    cfg = {
        "database_url": "postgresql://user:pass@localhost/db",
        "output_dir": "models",
        "enum_output_path": "enums",
        "relationship_mode": "invalid",
    }
    with pytest.raises(ConfigError) as e:
        validate_config(cfg)
    assert "relationship_mode must be 'minimal' or 'full'" in str(e.value)


def test_config_valid():
    cfg = {
        "database_url": "postgresql://user:pass@localhost/db",
        "output_dir": "models",
        "enum_output_path": "enums",
        "exclude_tables": ["foo"],
        "exclude_columns": ["bar"],
        "field_type_overrides": {"ARRAY": "CustomArrayType"},
        "relationship_mode": "full",
    }
    # Should not raise
    validate_config(cfg)
