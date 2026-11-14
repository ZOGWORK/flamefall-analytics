"""Extract per-test annotations from the Appendix B figure captions of the FLEX report.

Table IX does not record cool flames, droplet support, or extinction mode.
The figure captions in Appendix B of NASA/TP-2015-216046 (one figure per test)
do, in prose. This script pulls three things out of each caption and keeps the
exact sentence each label rests on:

  support            free-floating / fiber-supported   (first sentence of the caption)
  cool_flame         indicated / not_indicated / unclear / "" (caption silent)
  extinction_wording radiative / diffusive / both_mentioned / "" (caption silent)

Labels are assigned by the phrase rules below and were then read one by one
against the captions (see data/PROVENANCE.md). A silent caption stays empty:
it is NOT evidence that no cool flame occurred.

Usage:
    python scripts/extract_flex_captions.py path/to/20150023456.txt

Input: the NTRS full-text file,
https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.txt
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data" / "flex_caption_annotations.csv"
SOURCE_URL = "https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.txt"

NEGATIVE = re.compile(
    r"no evidence of (a |prolonged )?cool flame|probably no,? (or only very brief,? )?cool flame"
    r"|appears to be no cool flame|no cool flame", re.I)
UNCLEAR = re.compile(
    r"not clear|not known|not enough evidence|unclear|difficult to determine|cannot be determined|could not be determined"
    r"|not possible to determine|may or may not", re.I)


def normalise(text: str) -> str:
    for ch in "\u2010\u2011\u2012\u2013\u2014\u2212":
        text = text.replace(ch, "-")
    return text.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.])\s+(?=[A-Z])", text) if s.strip()]


def classify_cool(sents: list[str]) -> tuple[str, str]:
    hits = [s for s in sents if re.search(r"cool.flame", s, re.I)]
    if not hits:
        return "", ""
    quote = " ".join(hits)
    if any(UNCLEAR.search(s) for s in hits):
        return "unclear", quote
    if any(NEGATIVE.search(s) for s in hits):
        return "not_indicated", quote
    return "indicated", quote


def classify_ext(sents: list[str]) -> tuple[str, str]:
    rad = [s for s in sents if re.search(r"radiativ", s, re.I)]
    dif = [s for s in sents if re.search(r"diffusiv", s, re.I)]
    hedged = any(UNCLEAR.search(s) or re.search(r"radiative or diffusive|diffusive or radiative", s, re.I)
                 for s in rad + dif)
    quote = " ".join(dict.fromkeys(rad + dif))
    if not rad and not dif:
        return "", ""
    if hedged or (rad and dif):
        return "both_mentioned", quote
    return ("radiative" if rad else "diffusive"), quote


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    text = normalise(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))
    heads = list(re.finditer(r"^Figure (\d+)\.-Test FLEX-(\d{3})\.", text, re.M))
    rows = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.end():end]
        body = re.split(r"\n\s*NASA/TP", body)[0]          # stop at the page footer
        body = re.sub(r"-\n(?=[a-z])", "", body)            # undo line-break hyphenation
        body = " ".join(body.split())
        sents = sentences(body)
        first = sents[0] if sents else ""
        if re.search(r"free-floating|free floating|free-floated", first, re.I):
            support = "free-floating"
        elif re.search(r"fiber-supported|fiber supported|tethered|on (a|the) fiber", first, re.I):
            support = "fiber-supported"
        else:
            support = ""
        cool, cool_q = classify_cool(sents)
        ext, ext_q = classify_ext(sents)
        rows.append(dict(test_no=int(m.group(2)), figure_no=int(m.group(1)), support=support,
                         support_quote=first if support else "", cool_flame=cool,
                         cool_flame_quote=cool_q, extinction_wording=ext,
                         extinction_quote=ext_q,
                         source="NASA/TP-2015-216046, Appendix B, Figure %s caption" % m.group(1),
                         source_url=SOURCE_URL))
    rows.sort(key=lambda r: r["test_no"])
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print("captions:", len(rows))
    for col in ("support", "cool_flame", "extinction_wording"):
        print(col, dict(Counter(r[col] or "(silent)" for r in rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
