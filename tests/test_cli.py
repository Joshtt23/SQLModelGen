from typer.testing import CliRunner
from sqlmodelgen.cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SQLModelGen" in result.output
