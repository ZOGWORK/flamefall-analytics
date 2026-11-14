"""Stage 2 of Appendix A extraction: grid rows -> logical columns (no row merging yet).
usage: appx_logical.py <appx_cells.json> <out.json>
"""
import sys, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = json.load(open(sys.argv[1], encoding="utf-8"))
out = {}
for p in sorted(d):
    rows = d[p]["rows"]
    hdr = rows[0]
    logical = []  # [x0, x1, text]
    for c in hdr:
        t = " ".join(c["lines"]).strip()
        if not t:
            continue
        cont = t.startswith("(") or t == "potentiometer" or t.startswith("number (S/N)")
        if cont and logical:
            logical[-1][1] = c["bbox"][2]
            logical[-1][2] += " " + t
        else:
            logical.append([c["bbox"][0], c["bbox"][2], t])
    body = []
    for r in rows[1:]:
        rec = {}
        for c in r:
            if not c["lines"]:
                continue
            best, bo = None, 0.0
            for i, h in enumerate(logical):
                o = min(c["bbox"][2], h[1]) - max(c["bbox"][0], h[0])
                if o > bo:
                    best, bo = i, o
            assert best is not None, (p, c)
            assert str(best) not in rec, (p, best, c, rec)
            rec[str(best)] = c["lines"]
        body.append({"y0": r[0]["bbox"][1], "y1": r[0]["bbox"][3], "cells": rec})
    out[p] = {"header": [h[2] for h in logical], "body": body}
    print(p, len(logical), "logical columns;", len(body), "grid rows")
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
