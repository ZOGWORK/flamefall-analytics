"""Snapshot the PSI Data Repository records returned by a search for "combustion".

Uses only the public JSON endpoints that the PSI web application itself calls
(no login, no scraping of rendered pages):

  search    GET  https://psi.nasa.gov/geode-py/ws/repo/search?term=combustion&from=0&size=25
  record    GET  https://psi.nasa.gov/geode-py/ws/repo/investigations/<PSI-id>
  files     POST https://psi.nasa.gov/geode-py/ws/files/v2   {"folder":"","fileType":"study","studyId":..,"version":..}
  download  GET  https://psi.nasa.gov/geode-py/ws/studies/<PSI-id>/download?file=..&version=..&studyVersion=..&redirect=false

Writes, under data/psi/:
  search_combustion.json            the search hits, in PSI's relevance order
  records/<PSI-id>.json             each record's metadata as returned, minus the two
                                    version-diff blobs ('added', 'removed')
  files/<PSI-id>.json               a per-category summary of the record's file listing
  experimental_tables/<file>.csv    every "Experimental table" CSV attached to a record
  SNAPSHOT.json                     retrieval date, counts and endpoint list

Run from the repo root:  python scripts/fetch_psi.py
Standard library only.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://psi.nasa.gov/geode-py/ws"
OUT = Path(__file__).resolve().parents[1] / "data" / "psi"
HEADERS = {"User-Agent": "flamefall-analytics (open-source research dashboard)", "Accept": "application/json"}
TERM = "combustion"
DROP_KEYS = ("added", "removed")
CONTACT_KEY = re.compile(r"e-?mail|phone|fax|address", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def strip_contacts(node):
    """Remove contact details from a PSI record before it is written.

    Fields named for an e-mail address, phone, fax or postal address are dropped, and an e-mail
    address inside any other text is replaced. Names, roles and affiliations are kept.
    """
    if isinstance(node, dict):
        return {k: strip_contacts(v) for k, v in node.items() if not CONTACT_KEY.search(k)}
    if isinstance(node, list):
        return [strip_contacts(v) for v in node]
    if isinstance(node, str):
        return EMAIL.sub("[e-mail removed]", node)
    return node


def get(url: str, data: bytes | None = None, as_json: bool = True, tries: int = 3):
    headers = dict(HEADERS)
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=90) as r:
                body = r.read()
            return json.loads(body) if as_json else body
        except Exception as exc:  # noqa: BLE001 - network script; report and retry
            if attempt == tries - 1:
                raise
            print(f"  retry {attempt + 1} for {url[:90]}: {exc}")
            time.sleep(2 + 2 * attempt)


def walk_files(node: dict, category: str = "") -> list[dict]:
    """Flatten PSI's nested file listing into leaf files tagged with their top-level category."""
    out = []
    for child in node.get("files", []):
        cat = category or child.get("displayName") or child.get("sortingCategory") or ""
        if child.get("directory") or child.get("files"):
            out += walk_files(child, cat)
        elif child.get("key"):
            out.append({"key": child["key"], "bytes": child.get("bytes_size", 0), "version": child.get("version"),
                        "category": child.get("sortingCategory") or cat, "restricted": bool(child.get("restricted"))})
    return out


def main() -> int:
    for sub in ("records", "files", "experimental_tables"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)
    hits, total, start = [], None, 0
    while total is None or start < total:
        page = get(f"{BASE}/repo/search?term={TERM}&from={start}&size=25")
        total = page["hits"]["total"]
        total = total["value"] if isinstance(total, dict) else total
        hits += page["hits"]["hits"]
        start += 25
    print(f"search '{TERM}': {total} hits, {len(hits)} fetched")
    (OUT / "search_combustion.json").write_text(json.dumps(
        [{"rank": i + 1, "score": h.get("_score"), **strip_contacts(h["_source"])} for i, h in enumerate(hits)],
        indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    tables, summary = [], []
    for i, h in enumerate(hits):
        src = h["_source"]
        psi_id = src.get("Accession") or src.get("accession") or h.get("_id")
        rec = get(f"{BASE}/repo/investigations/{psi_id}")
        for bulky in DROP_KEYS:          # version-diff blobs, megabytes each, not record content
            rec.pop(bulky, None)
        rec = strip_contacts(rec)
        (OUT / "records" / f"{psi_id}.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n",
                                                        encoding="utf-8")
        version = rec.get("versionInfo", {}).get("version") or rec.get("version") or 1
        body = json.dumps({"folder": "", "fileType": "study", "studyId": psi_id, "version": version}).encode()
        leaves = walk_files(get(f"{BASE}/files/v2", data=body))
        by_cat: dict[str, dict] = {}
        for leaf in leaves:
            c = by_cat.setdefault(leaf["category"] or "(uncategorised)", {"files": 0, "bytes": 0})
            c["files"] += 1
            c["bytes"] += leaf["bytes"] or 0
        exp = [leaf for leaf in leaves if "experimental table" in leaf["key"].lower() and leaf["key"].lower().endswith(".csv")]
        (OUT / "files" / f"{psi_id}.json").write_text(json.dumps(
            {"psi_id": psi_id, "record_version": version, "file_count": len(leaves),
             "total_bytes": sum(leaf["bytes"] or 0 for leaf in leaves), "by_category": by_cat,
             "experimental_tables": [Path(leaf["key"]).name for leaf in exp]}, indent=1) + "\n", encoding="utf-8")
        for leaf in exp:
            name = Path(leaf["key"]).name
            q = urllib.parse.urlencode({"file": name, "version": leaf["version"], "studyVersion": version,
                                        "redirect": "false"}, quote_via=urllib.parse.quote)
            signed = get(f"{BASE}/studies/{psi_id}/download?{q}", as_json=False).decode().strip().strip('"')
            (OUT / "experimental_tables" / name).write_bytes(get(signed, as_json=False))
            tables.append(name)
        summary.append({"rank": i + 1, "psi_id": psi_id, "files": len(leaves), "tables": len(exp)})
        print(f"  {i + 1:2d} {psi_id:8s} files={len(leaves):4d} experimental tables={len(exp)}")
        time.sleep(0.3)

    (OUT / "SNAPSHOT.json").write_text(json.dumps({
        "retrieved_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "search_term": TERM, "search_hits": total, "records": summary, "experimental_tables": sorted(tables),
        "endpoints": [f"{BASE}/repo/search", f"{BASE}/repo/investigations/<id>", f"{BASE}/files/v2",
                      f"{BASE}/studies/<id>/download"],
        "human_record_url": "https://psi.nasa.gov/physci/repo/data/investigations/<id>",
    }, indent=1) + "\n", encoding="utf-8")
    print(f"done: {len(summary)} records, {len(tables)} experimental tables")
    return 0


if __name__ == "__main__":
    sys.exit(main())
