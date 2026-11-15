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


# ---------------------------------------------------------------- the README's numbers and links

def _readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_headline_numbers_are_the_ones_in_the_data():
    """Every number in the README's two findings tables is recomputed here from the data files."""
    import json

    from flamefall import catalogue as cat
    from flamefall import flex

    text = _readme()
    s, c = flex.summary(), cat.counts()
    o, m, h = s["outcomes"], s["by_fuel"]["Methanol"], s["by_fuel"]["Heptane"]
    solid = cat.load_solid_points()
    decided = int((solid["outcome"] != "ambiguous").sum())
    limit = cat.load_evidence().set_index("id").loc["sofie-gel-envelope", "o2_max_pct"]
    partial_g = cat.load_investigations()
    partial_g = partial_g[partial_g["in_psi_search"] & (partial_g["status"] != "planned")]
    gravity = [cat._num(v) for v in partial_g["gravity_g"]]
    expected = [
        f"{s['n']} tests: {o['Extinction']} Extinction, {o['Disruption']} Disruption, {o['Completion']} Completion",
        f"Extinction in {m['Extinction']} of {m['n']} methanol tests and {h['Extinction']} of {h['n']} n-heptane tests",
        f"{s['cool_flame']['indicated']} of {s['heptane_extinctions']} n-heptane extinctions",
        f"{c['search_hits']} records, {c['combustion_science']} of them combustion science, {c['tables']} experimental tables",
        f"{len(solid)} transcribed, {decided} with a stated outcome; the highest oxygen among them is "
        f"{solid['o2_at_outcome_pct'].max():g}%",
        f"extinction limits mapped over that range). The data files hold no solid-material test point above {limit:g}% |",
        f"{c['evidence']}, of which {c['evidence_verified']} were verified against the source they cite",
    ]
    for sentence in expected:
        assert sentence in text, sentence
    assert solid["o2_at_outcome_pct"].max() == cat.solid_envelope()["o2"][1] < limit
    # "an investigation that has flown": a planned experiment (FM2) names higher oxygen levels, and it
    # is solid fuel. It is left out here by its status, not by whether its range happens to be recorded.
    ev = cat.load_evidence()
    inv = cat.load_investigations()
    planned = set(inv.loc[inv["status"] == "planned", "investigation_id"])
    assert planned == {"FM2"}
    flown = ev[ev["evidence_class"].isin(["solid", "partial_g"]) & ev["o2_is_ambient"].astype(bool)
               & ~ev["investigation_id"].isin(planned)]
    assert len(flown) > 20 and flown["o2_max_pct"].max() == limit
    gel = ev.set_index("id").loc["sofie-gel-envelope"]
    assert f"| {gel['o2_min_pct']:g} to {gel['o2_max_pct']:g}% (SoFIE-GEL, extinction limits mapped over that range)" in text
    assert "mapped" in gel["statement"]                             # the README uses the statement's own word
    assert "T'ien et al." in gel["source_ref"] and "Range: T'ien et al., Combust. Flame 277 (2025) 114244." in text
    assert "37" in ev.set_index("id").loc["fm2-plan", "statement"] and "planned" in ev.set_index("id").loc["fm2-plan", "statement"]
    assert "reported by a solid-fuel investigation that has flown" in text
    assert "investigation states" not in text and "investigation has tested" not in text
    # every statement counted as verified names the source it was checked against and how it was read;
    # a verbatim quote is stored for some, and the disclosure gives that count
    verified = ev[ev["verification"] == "verified_live"]
    assert len(verified) == c["evidence_verified"]
    assert verified["source_ref"].str.len().gt(0).all() and verified["read_level"].str.len().gt(0).all()
    assert "primary source |" not in text
    quoted = int(ev["quote"].fillna("").str.strip().ne("").sum())
    disclosure = (ROOT / "docs" / "SI_DISCLOSURE.md").read_text(encoding="utf-8")
    assert f"a verbatim quote is stored for {quoted} of the {len(ev)}" in disclosure
    assert "a verbatim quote and the read level stored" not in disclosure

    # the partial-gravity count sits in its own row, not just anywhere on the page
    count = sum(1 for g in gravity if g is not None and 0.05 < g < 0.5)
    row = next(line for line in text.splitlines()
               if line.startswith("| Combustion tests in lunar or Martian gravity in the repository |"))
    assert [cell.strip() for cell in row.split("|")][2] == str(count) == "0"

    cards = {n: json.loads((ROOT / "data" / "models" / f"{n}.json").read_text(encoding="utf-8"))
             for n in ("droplet_extinction", "droplet_cool_flame", "solid_sustained")}
    ext, cool, sol = cards["droplet_extinction"], cards["droplet_cool_flame"], cards["solid_sustained"]
    rows = [
        f"| {ext['n_rows']} | {ext['metrics']['roc_auc']:.2f} grouped cross-validation, {ext['headline_auc']:.2f} on an unseen fuel",
        f"| {cool['n_rows']} | {cool['headline_auc']:.2f}, exploratory",
        f"| {sol['n_rows']} | {sol['headline_auc']:.2f}, no better than chance",
    ]
    for row in rows:
        assert row in text, row
    assert ext["headline_is"] == "leave-one-material-out" and sol["headline_auc"] < 0.6


def test_every_local_link_in_the_readme_files_points_at_something_that_exists():
    import re

    files = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "docs" / "README.md", ROOT / "scripts" / "README.md",
             ROOT / "web" / "README.md"]
    checked = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)#]+)\)", text):
            if target.startswith(("http://", "https://")):
                continue
            assert (path.parent / target).exists(), f"{path.relative_to(ROOT)} links to {target}"
            checked += 1
    assert checked >= 15
    for name in ("overview.png", "scenario-lab.png"):
        assert (ROOT / "docs" / "img" / name).stat().st_size > 50_000, name


def test_readme_names_every_script_and_every_page():
    scripts = (ROOT / "scripts" / "README.md").read_text(encoding="utf-8")
    for script in sorted((ROOT / "scripts").glob("*.py")):
        assert f"`{script.name}`" in scripts, script.name
    text = _readme()
    for route in ("", "flex/", "catalogue/", "scenario/", "models/", "unknowns/"):
        assert f"(https://flamefall-analytics.onrender.com/{route})" in text, route     # the whole link target
    assert "https://flamefall-analytics.onrender.com/deck/\n" in text
