from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from sqlmodelgenerator.cli import app

runner = CliRunner()


@patch("sqlmodelgenerator.cli.load_config")
@patch("sqlmodelgenerator.cli.Introspector")
@patch("sqlmodelgenerator.cli.ModelGenerator")
def test_generate_command(
    mock_modelgen, mock_introspector, mock_load_config, tmp_path
) -> None:
    # Create a dummy config file
    config_path = tmp_path / "fake.yaml"
    config_path.write_text(
        "database_url: postgresql://user:pass@localhost/db\noutput_dir: models\n"
        "enum_output_path: enums\n"
    )
    # Create output and enum directories
    (tmp_path / "models").mkdir()
    (tmp_path / "enums").mkdir()
    # Mock config
    mock_load_config.return_value = {
        "database_url": "postgresql://user:pass@localhost/db",
        "output_dir": str(tmp_path / "models"),
        "enum_output_path": str(tmp_path / "enums"),
        "field_type_overrides": {},
    }
    # Mock introspector
    mock_introspect_instance = MagicMock()
    mock_introspect_instance.get_tables.return_value = ["user"]
    mock_introspect_instance.get_enums.return_value = {
        "UserStatus": ["active", "inactive"]
    }
    mock_introspect_instance.get_columns.return_value = [
        {"name": "id", "type": "INTEGER", "nullable": False},
        {
            "name": "status",
            "type": "user_status",
            "nullable": False,
            "enum_name": "UserStatus",
        },
    ]
    mock_introspect_instance.get_foreign_keys.return_value = []
    mock_introspector.return_value = mock_introspect_instance
    # Mock ModelGenerator
    mock_modelgen_instance = MagicMock()
    mock_modelgen.return_value = mock_modelgen_instance
    result = runner.invoke(app, ["generate", "--config", str(config_path)])
    assert result.exit_code == 0
    assert "Model and enum generation complete!" in result.output
    mock_modelgen_instance.generate_enum.assert_called_with(
        "Userstatus", ["active", "inactive"]
    )
    mock_modelgen_instance.generate_model.assert_called()
    mock_modelgen_instance.write_enum_file.assert_called()
    mock_modelgen_instance.write_model_file.assert_called()


@patch("sqlmodelgenerator.cli.load_config")
@patch("sqlmodelgenerator.cli.Introspector")
def test_inspect_command(mock_introspector, mock_load_config) -> None:
    mock_load_config.return_value = {
        "database_url": "postgresql://user:pass@localhost/db"
    }
    mock_introspect_instance = MagicMock()
    mock_introspect_instance.get_tables.return_value = ["user"]
    mock_introspect_instance.get_enums.return_value = {
        "UserStatus": ["active", "inactive"]
    }
    mock_introspect_instance.get_columns.return_value = [
        {"name": "id", "type": "INTEGER", "nullable": False},
        {
            "name": "status",
            "type": "user_status",
            "nullable": False,
            "enum_name": "UserStatus",
        },
    ]
    mock_introspect_instance.get_foreign_keys.return_value = []
    mock_introspector.return_value = mock_introspect_instance
    result = runner.invoke(app, ["inspect", "--config", "fake.yaml"])
    assert result.exit_code == 0
    assert "Tables:" in result.output
    assert "user" in result.output
    assert "Enums:" in result.output
    assert "UserStatus" in result.output
