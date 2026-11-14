"""Documentation checks: the README's commands must be usable on every platform."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def readme_code_lines() -> list[str]:
    """Every line inside a fenced block of the README, comments included."""
    in_block, lines = False, []
    for line in (ROOT / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_block = not in_block
        elif in_block:
            lines.append(line)
    return lines


def test_readme_commands_do_not_hardcode_a_platform_venv_path():
    commands = [line.split("#")[0].strip() for line in readme_code_lines()]
    # the interpreter is always plain `python` from an activated environment
    assert not any(c.startswith((".venv/Scripts/python", ".venv/bin/python", ".venv\\Scripts\\python"))
                   for c in commands)
    assert "python scripts/build_flex_droplets.py" in commands
    assert "python scripts/export_web.py" in commands
    assert {"npm ci", "npm run dev", "npm run test", "npm run build"} <= set(commands)
    assert "python -m pytest" in commands


def test_readme_gives_an_activation_command_for_each_platform():
    text = "\n".join(readme_code_lines())
    assert ".venv/bin/activate" in text              # macOS / Linux
    assert ".venv\\Scripts\\activate" in text        # Windows
