"""Build index.html: the same Streamlit app, running entirely in the browser.

The page loads stlite (Streamlit compiled to WebAssembly through Pyodide) and mounts this
repository's own `app.py`, `flamefall/`, `views/` and `data/` files by URL. Nothing is copied or
rewritten: the browser version runs the very files the tests run. It needs no server and no
account, so it can be hosted on GitHub Pages from the repository root.

Run from the repo root:  python scripts/build_web.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STLITE = "1.12.0"          # bundles Streamlit 1.65.0
REQUIREMENTS = ["pandas", "numpy", "plotly", "scikit-learn"]
INCLUDE = ["app.py", "flamefall/*.py", "views/*.py", "data/*.csv", "data/*.json", "data/models/*.json",
           "data/psi/*.json", "data/psi/records/*.json", "data/psi/files/*.json",
           "data/psi/experimental_tables/*.csv", "data/bass2/*.csv"]
CONFIG = {
    "theme.base": "dark", "theme.primaryColor": "#F59E0B", "theme.backgroundColor": "#0B0F14",
    "theme.secondaryBackgroundColor": "#111821", "theme.textColor": "#E6EDF3",
    "client.toolbarMode": "minimal", "client.showErrorDetails": False,
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<title>Flamefall Analytics</title>
<meta name="description" content="What microgravity combustion experiments actually measured, for crewed spacecraft fire protection. Every number carries its source.">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@stlite/browser@__STLITE__/build/stlite.css">
<style>
  html, body {{ margin: 0; height: 100%; background: #0B0F14; color: #E6EDF3; font-family: system-ui, sans-serif; }}
  #boot {{ position: fixed; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
          gap: 10px; text-align: center; padding: 24px; background: #0B0F14; z-index: 2; }}
  #boot b {{ font: 700 0.8rem ui-monospace, Menlo, Consolas, monospace; letter-spacing: .18em; text-transform: uppercase; color: #F59E0B; }}
  #boot p {{ margin: 0; color: #9AA7B6; max-width: 46ch; line-height: 1.5; }}
  #boot a {{ color: #22D3EE; }}
  /* stlite positions the app absolutely inside this element, so it must fill the viewport.
     The loading note sits above it (z-index 2) so its links work, and is removed once the app draws. */
  #root {{ position: fixed; inset: 0; z-index: 1; }}
</style>
</head>
<body>
<div id="boot">
  <b>Flamefall Analytics</b>
  <p>Loading the dashboard. The first visit downloads the Python runtime and can take up to a minute; after that it opens quickly.</p>
  <p><a href="deck/">Open the 7-slide summary</a> · <a href="https://github.com/ZOGWORK/flamefall-analytics">Code and data</a></p>
  <noscript><p>This dashboard needs JavaScript. The code and data are in the repository linked above.</p></noscript>
</div>
<div id="root"></div>
<script type="module">
import {{ mount }} from "https://cdn.jsdelivr.net/npm/@stlite/browser@__STLITE__/build/stlite.js";
const paths = __PATHS__;
// The version is a hash of every mounted file, so a browser never mixes a cached file with a new build.
const version = "__VERSION__";
const files = Object.fromEntries(paths.map((p) => [p, {{ url: new URL(p + "?v=" + version, window.location.href).href }}]));
const root = document.getElementById("root");
mount({{
  entrypoint: "app.py",
  requirements: __REQUIREMENTS__,
  files,
  streamlitConfig: __CONFIG__,
}}, root);
// Drop the loading note once the app has drawn its first heading.
new MutationObserver((_, observer) => {{
  if (root.querySelector('[data-testid="stMain"] h1')) {{
    document.getElementById("boot")?.remove();
    observer.disconnect();
  }}
}}).observe(root, {{ childList: true, subtree: true }});
</script>
</body>
</html>
"""


# The app changes the address bar as you move between pages (/scenario, /model, ...). On a static
# host those addresses do not exist, so a reload or a shared deep link lands here and is sent home.
NOT_FOUND = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Flamefall Analytics</title>
<meta http-equiv="refresh" content="0; url=/flamefall-analytics/">
<script>location.replace("/flamefall-analytics/");</script>
</head>
<body style="background:#0B0F14;color:#E6EDF3;font-family:system-ui,sans-serif;padding:2rem">
<p>Opening the dashboard at <a style="color:#22D3EE" href="/flamefall-analytics/">zogwork.github.io/flamefall-analytics</a>.</p>
</body>
</html>
"""


def collect() -> list[str]:
    paths: list[str] = []
    for pattern in INCLUDE:
        paths += sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob(pattern))
    return paths


def content_version(paths: list[str]) -> str:
    """Short hash of the mounted files' contents (line endings normalised so it is the same on every OS)."""
    digest = hashlib.sha256()
    for p in paths:
        digest.update(p.encode())
        digest.update((ROOT / p).read_bytes().replace(b"\r\n", b"\n"))
    return digest.hexdigest()[:12]


def main() -> int:
    paths = collect()
    html = (PAGE.replace("{{", "{").replace("}}", "}")
            .replace("__STLITE__", STLITE)
            .replace("__VERSION__", content_version(paths))
            .replace("__PATHS__", json.dumps(paths, indent=1))
            .replace("__REQUIREMENTS__", json.dumps(REQUIREMENTS))
            .replace("__CONFIG__", json.dumps(CONFIG)))
    (ROOT / "index.html").write_text(html, encoding="utf-8", newline="\n")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")     # GitHub Pages: serve files as they are
    (ROOT / "404.html").write_text(NOT_FOUND, encoding="utf-8", newline="\n")
    size = sum((ROOT / p).stat().st_size for p in paths)
    print(f"wrote index.html: {len(paths)} files mounted, {size / 1e6:.1f} MB, stlite {STLITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
