"""Wording rules that the science depends on, checked across every file whose text reaches a reader."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READER_FACING = (
    sorted((ROOT / "flamefall").glob("*.py"))
    + [ROOT / "data" / "evidence.json", ROOT / "data" / "investigations_curated.json", ROOT / "README.md"]
    + sorted((ROOT / "data" / "models").glob("*.json"))
    + [ROOT / "data" / "panels.json"]
    + sorted((ROOT / "web" / "src" / "data").glob("*.json"))          # what the web app reads
    + sorted(p for ext in ("*.ts", "*.tsx") for p in (ROOT / "web" / "src").rglob(ext))
    + sorted((ROOT / "docs").glob("*.md"))
    + [ROOT / "CONTRIBUTING.md", ROOT / "scripts" / "README.md", ROOT / "web" / "README.md"]
)
VERDICT = re.compile(r"\b(safe|unsafe|certified|certification|certify)\b", re.I)
EIGHTY_FIVE = re.compile(r"\b85\s?%|\b0\.85\b|\b85 percent")
OXYGEN = re.compile(r"oxygen|\bO2\b|XO2", re.I)
QUALIFIER = re.compile(r"burner|inverse", re.I)
MIXTURE = re.compile(r"^(\d(?:\.\d+)?(?:/\d(?:\.\d+)?)+) ([A-Za-z0-9]+(?:/[A-Za-z0-9]+)+)$")


def says_85_percent_oxygen(text: str) -> bool:
    """True when a text gives 85% as an oxygen value.

    A gas mixture written as "0.15/0.85 O2/N2" pairs values with gases by position, so there the
    oxygen value is read from its own position and a nitrogen fraction of 0.85 is not a match.
    """
    mixture = MIXTURE.match(text.strip())
    if mixture:
        fractions = dict(zip(mixture.group(2).split("/"), mixture.group(1).split("/")))
        return float(fractions.get("O2", 0)) == 0.85
    return bool(EIGHTY_FIVE.search(text) and OXYGEN.search(text))


def strings(node):
    """Every text value inside a parsed JSON document."""
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from strings(value)


def lines(path: Path):
    """The units a rule is applied to: lines of a text file, or each text value of a JSON file.

    A JSON file may be written on a single line, so its lines mean nothing; its values do.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        for number, value in enumerate(strings(json.loads(text)), 1):
            yield number, value
    else:
        for number, line in enumerate(text.splitlines(), 1):
            yield number, line


def test_no_verdict_wording_anywhere():
    """Nothing may be called safe or certified. ('Safety' as a field of study is fine.)"""
    hits = [f"{p.relative_to(ROOT)}:{n}: {line.strip()[:120]}" for p in READER_FACING for n, line in lines(p)
            if VERDICT.search(line)]
    assert not hits, "\n".join(hits)


def test_every_85_percent_oxygen_value_is_labelled_as_a_burner_feed():
    hits = [f"{p.relative_to(ROOT)}:{n}: {line.strip()[:140]}" for p in READER_FACING for n, line in lines(p)
            if says_85_percent_oxygen(line) and not QUALIFIER.search(line)]
    assert not hits, "\n".join(hits)


def test_the_85_percent_rule_reads_gas_mixture_notation_by_position():
    assert says_85_percent_oxygen("tested at 85% O2")
    assert says_85_percent_oxygen("burner oxygen mole fraction of 0.85")
    assert not says_85_percent_oxygen("0.15/0.85 O2/N2")              # 0.85 is the nitrogen fraction
    assert says_85_percent_oxygen("0.85/0.15 O2/N2")
    assert not says_85_percent_oxygen("85% of tests")


def test_the_disconfirmed_phrase_is_absent():
    for p in READER_FACING:
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"CFI-G up to 85", text, re.I), p.name
        assert not re.search(r"NET late 2026", text, re.I), p.name      # stale launch date for the lunar experiment


def test_no_single_burning_rate_is_quoted_for_n_heptane():
    """0.39 mm2/s is n-decane and 0.378-0.398 is n-dodecane: neither may be attached to heptane."""
    for p in READER_FACING:
        for _, line in lines(p):
            if re.search(r"heptane", line, re.I):
                assert not re.search(r"\b0\.39\b|0\.378|0\.398", line), f"{p.name}: {line.strip()[:120]}"


OWN_SCREENSHOTS = {"docs/img/overview.png", "docs/img/scenario-lab.png"}
OWN_IMAGES = OWN_SCREENSHOTS | {"web/src/app/icon.svg"}
IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico", ".avif", ".bmp", ".tif", ".tiff", ".heic",
                  ".heif", ".jxl", ".apng")
# A whole token (everything up to white space, a quote, a bracket or a backtick) that ends in an
# image suffix. Taking the whole token means an address that merely contains an allowed path
# ("https://elsewhere/get?u=docs/img/overview.png") is not mistaken for that path.
IMAGE_FILE = re.compile(r"""[^\s"'()<>\[\]`]*\.(?:png|jpe?g|svg|gif|webp|ico|avif|bmp|tiff?|heic|heif|jxl|apng)\b""", re.I)
MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]*)[^)]*\)")
# elements that can show a picture. In Markdown, HTML tags are matched in any letter case. In
# TypeScript only the lower-case HTML elements and next/image count: `<Source>` is a component here.
PICTURE_TAG_HTML = re.compile(r"<\s*(img|image|picture|source|video|object|embed|iframe|svg)\b", re.I)
PICTURE_TAG_TSX = re.compile(r"<(img|image|picture|source|video|object|embed|iframe)\b|<Image\b|next/image")
CSS_URL = re.compile(r"(?<![\w.])url\(\s*([^)]*)\)")          # the CSS function, not a name that ends in "url"
IMAGE_CHECKED = READER_FACING + [ROOT / "web" / "src" / "app" / "globals.css"]
# the liquid-glass surface builds its displacement maps as SVG text in code; they are not pictures
COMPUTED_SVG_ONLY = {"liquid-glass.tsx"}


def foreign_images(name: str, text: str) -> list[str]:
    """Every way this text could show an image that is not one of the project's own.

    Caught: a file name or address ending in an image suffix; in Markdown, any `![` that is not an
    inline image of one of the two screenshots (so a reference-style image fails too) and any HTML
    element that can show a picture, in any letter case; in every other file, the lower-case picture
    elements and next/image; an inline `data:image`; a CSS `url(...)` that is not a reference to an
    element on the page. A picture loaded in some other way would need a new check here.
    """
    found = [t for t in IMAGE_FILE.findall(text) if t not in OWN_IMAGES]
    inline = MARKDOWN_IMAGE.findall(text)
    found += [f"markdown image: {t}" for t in inline if t not in OWN_SCREENSHOTS]
    if name.endswith(".md"):
        if text.count("![") != len(inline):
            found.append("a Markdown image that is not written inline")
        if PICTURE_TAG_HTML.search(text):
            found.append("an HTML picture element")
    elif PICTURE_TAG_TSX.search(text):
        found.append("a picture element")
    if "data:image" in text and name not in COMPUTED_SVG_ONLY:
        found.append("an inline data:image")
    found += [f"css url: {t}" for t in CSS_URL.findall(text) if not t.strip().strip("\"'").startswith("#")]
    return found
NOT_SOURCE = {".git", ".venv", "node_modules", ".next", "out", "__pycache__", ".pytest_cache"}


def repository_files() -> list[str]:
    """Files git tracks; in a copy with no git history (a downloaded archive), every file outside build folders."""
    import subprocess

    try:
        listed = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        listed = None
    if listed is not None and listed.returncode == 0 and listed.stdout.strip():
        return listed.stdout.split("\n")
    return [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
            if p.is_file() and not NOT_SOURCE & set(p.relative_to(ROOT).parts)]


def test_the_only_image_files_in_the_repository_are_the_icon_and_the_two_screenshots():
    images = {f for f in repository_files() if f.lower().endswith(IMAGE_SUFFIXES)}
    assert images == OWN_IMAGES, sorted(images)


def test_the_image_rule_catches_an_image_however_it_is_referenced():
    """The rule must fail for a foreign image in each way one can be written, or it proves nothing."""
    for text in ("![](https://example.org/nasa-logo.png?x=1)", "<img src=logo.png>", "[logo]: assets/logo.png",
                 "see patch.webp", 'src="/meatball.SVG"', "background: url(insignia.jpeg)", "favicon.ico",
                 "![](data:image/png;base64,AAAA)", '<img src="https://images.example/abc123">',
                 "https://elsewhere.example/get?u=docs/img/overview.png", "photo.heic", "![x](https://images.example/abc123)",
                 "background: url(https://images.example/abc123)",
                 "x,docs/img/overview.png", "![logo][l]\n\n[l]: https://images.example/abc",
                 '<IMG SRC="https://x.example/a">', '<picture><source srcset="https://x.example/a"></picture>',
                 '<svg><image href="https://x.example/a"/></svg>', "< img src=x>"):
        assert foreign_images("README.md", text) != [], text
    for text in ('<img src="https://x.example/a" />', '<picture><source srcSet="https://x.example/a" /></picture>',
                 '<image href="https://x.example/a" />', 'import Image from "next/image"', "<Image src={x} />"):
        assert foreign_images("page.tsx", text) != [], text
    for text in ("<Source href={url}>text</Source>", "<feImage href={map} />", "<ImageIcon />", "<svg viewBox='0 0 1 1' />"):
        assert foreign_images("page.tsx", text) == [], text
    for text in ("![Overview](docs/img/overview.png)", "`web/src/app/icon.svg`", "(docs/img/scenario-lab.png)",
                 "no image here: config.json, icon={Flame}, a.pngx", "fill=\"url(#grad-1)\"", "filter: url(#${filterId})"):
        assert foreign_images("README.md", text) == [], text
    assert foreign_images("liquid-glass.tsx", "`data:image/svg+xml,${encodeURIComponent(svg)}`") == []
    assert foreign_images("page.tsx", "`data:image/svg+xml,${encodeURIComponent(svg)}`") != []


def test_no_agency_marks_are_referenced():
    """No logo, insignia or mission-patch image is referenced anywhere."""
    for p in READER_FACING:
        text = p.read_text(encoding="utf-8")
        assert not re.search(r"<img[^>]+(nasa|meatball|insignia|patch)", text, re.I), p.name
    for p in IMAGE_CHECKED:
        assert foreign_images(p.name, p.read_text(encoding="utf-8")) == [], p.name
