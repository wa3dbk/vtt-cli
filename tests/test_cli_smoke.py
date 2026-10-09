from click.testing import CliRunner
from vtt_clean.cli import main

def test_cli_help_exits_zero():
    result = CliRunner().invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "process" in result.output or "Usage" in result.output
