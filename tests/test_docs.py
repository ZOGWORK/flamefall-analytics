"""Documentation checks: commands in the README must work on any platform."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def readme_commands() -> list[str]:
    in_block, commands = False, []
    for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_block = not in_block
        elif in_block:
            commands.append(line.split("#")[0].strip())
    return commands


def test_readme_commands_do_not_hardcode_a_platform_venv_path():
    commands = readme_commands()
    assert not any(".venv/Scripts/python" in c or ".venv/bin/python" in c for c in commands)
    assert "python -m streamlit run app.py" in commands
    assert "python -m pytest" in commands
    assert "source .venv/bin/activate" in commands          # one activation, then plain `python`
