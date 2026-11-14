"""Shared helpers for the BASS-II table extraction.
Cell geometry comes from pdfplumber (ruling lines); characters come from pymupdf spans
(correct Unicode, superscript flag). Nothing here interprets values.
"""
import pdfplumber, pymupdf

def page_spans(mupage):
    """Yield (x0,y0,x1,y1,text,is_super,block,line,span_idx) for every non-blank span."""
    d = mupage.get_text("dict")
    out = []
    for bi, b in enumerate(d["blocks"]):
        if b.get("type") != 0:
            continue
        for li, l in enumerate(b["lines"]):
            for si, s in enumerate(l["spans"]):
                if not s["text"].strip():
                    continue
                x0, y0, x1, y1 = s["bbox"]
                out.append((x0, y0, x1, y1, s["text"], bool(s["flags"] & 1), bi, li, si, s["size"]))
    return out

def grid_tables(pdf_path, pno):
    """Return list of tables; each table = {'bbox':..., 'rows': [[cell,...],...]} where
    cell = {'bbox':[x0,y0,x1,y1], 'lines':[str], 'sup':[str]} (sup = superscript spans)."""
    with pdfplumber.open(pdf_path) as pl:
        tabs = pl.pages[pno - 1].find_tables()
        geo = [(t.bbox, [[c for c in r.cells if c is not None] for r in t.rows]) for t in tabs]
    mu = pymupdf.open(pdf_path)
    spans = page_spans(mu[pno - 1])
    used = [False] * len(spans)
    tables = []
    for bbox, rows in geo:
        trows = []
        for r in rows:
            cells = []
            for (x0, y0, x1, y1) in r:
                got = []
                for i, s in enumerate(spans):
                    cx, cy = (s[0] + s[2]) / 2, (s[1] + s[3]) / 2
                    if not used[i] and x0 <= cx <= x1 and y0 <= cy <= y1:
                        used[i] = True
                        got.append(s)
                got.sort(key=lambda s: (s[6], s[7], s[8]))
                lines, sup, key, cur = [], [], None, ""
                for s in got:
                    if s[5]:
                        sup.append(s[4].strip())
                        continue
                    k = (s[6], s[7])
                    if key is not None and k != key:
                        lines.append(cur.strip()); cur = ""
                    key = k
                    cur += s[4]
                if cur.strip():
                    lines.append(cur.strip())
                cells.append({"bbox": [x0, y0, x1, y1], "lines": lines, "sup": sup})
            trows.append(cells)
        left = [s[4] for i, s in enumerate(spans) if not used[i]
                and bbox[0] <= (s[0] + s[2]) / 2 <= bbox[2] and bbox[1] <= (s[1] + s[3]) / 2 <= bbox[3]]
        tables.append({"bbox": list(bbox), "rows": trows, "leftover": left})
    return tables
