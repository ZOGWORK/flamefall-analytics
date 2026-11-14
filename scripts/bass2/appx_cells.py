"""Stage 1 of Appendix A extraction.
For each Appendix A page: take the cell grid from pdfplumber (ruling lines), take the
words from pymupdf (correct Unicode, reading order for rotated header text), put each
word into the grid cell that contains its centre, map each body cell onto a header
("logical") column by horizontal overlap, and write the raw grid rows to JSON.
No merging or interpretation happens here.
usage: appx_cells.py <pdf> <out.json>
"""
import sys, json
import pdfplumber, pymupdf

pdf_path, out_path = sys.argv[1], sys.argv[2]
PAGES = range(111, 122)
out = {}
with pdfplumber.open(pdf_path) as pl:
    mu = pymupdf.open(pdf_path)
    for pno in PAGES:
        ppage = pl.pages[pno - 1]
        tables = ppage.find_tables()
        assert len(tables) == 1, (pno, len(tables))
        tab = tables[0]
        words = mu[pno - 1].get_text("words")  # x0,y0,x1,y1,text,block,line,wno
        used = [False] * len(words)
        rows = []
        reordered = 0
        for ri, r in enumerate(tab.rows):
            cells = []
            for c in r.cells:
                if c is None:
                    continue
                x0, y0, x1, y1 = c
                ws = []
                for i, w in enumerate(words):
                    cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
                    if x0 <= cx <= x1 and y0 <= cy <= y1 and not used[i]:
                        used[i] = True
                        ws.append(w)
                # group words into pymupdf text lines (block, line); words stay in pymupdf order
                groups = {}
                for w in sorted(ws, key=lambda w: (w[5], w[6], w[7])):
                    groups.setdefault((w[5], w[6]), []).append(w)
                glist = list(groups.values())
                if ri > 0:
                    # body cells hold horizontal text: order the lines top-to-bottom, then left-to-right
                    by_y = sorted(glist, key=lambda g: (round(min(w[1] for w in g), 0), min(w[0] for w in g)))
                    if by_y != glist:
                        reordered += 1
                    glist = by_y
                lines = [" ".join(w[4] for w in g) for g in glist]
                cells.append({"bbox": [round(v, 2) for v in c], "lines": lines})
            rows.append(cells)
        tb = tab.bbox
        leftovers = [[round(w[0], 1), round(w[1], 1), w[4]] for i, w in enumerate(words)
                     if not used[i] and tb[0] <= (w[0] + w[2]) / 2 <= tb[2] and tb[1] <= (w[1] + w[3]) / 2 <= tb[3]]
        outside = " ".join(w[4] for i, w in enumerate(words) if not used[i]
                           and not (tb[0] <= (w[0] + w[2]) / 2 <= tb[2] and tb[1] <= (w[1] + w[3]) / 2 <= tb[3]))
        out[pno] = {"table_bbox": [round(v, 2) for v in tb], "rows": rows,
                    "leftover_in_table": leftovers, "outside_text": outside}
        print(pno, "grid rows", len(rows), "leftover words inside table bbox:", len(leftovers), "cells whose line order was changed by y-sort:", reordered)
json.dump(out, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
