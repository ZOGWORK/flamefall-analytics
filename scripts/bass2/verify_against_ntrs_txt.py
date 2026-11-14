"""Second, independent check: compare CSV cells with the NTRS full-text file (a different text extraction).
Row-order is not guaranteed there, so the test is per cell: the whitespace-free cell text must occur in the
whitespace-free NTRS text.  usage: verify_against_ntrs_txt.py <ntrs.txt> <out_dir>"""
import sys, os, io, csv, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
txt = re.sub(r"\s+", "", open(sys.argv[1], encoding="utf-8", errors="replace").read())
out_dir = sys.argv[2]
def read(n): return list(csv.DictReader(open(os.path.join(out_dir, n), encoding="utf-8", newline="")))
def sq(s): return re.sub(r"\s+", "", s)
for name, key, skip in (("table_5_1.csv", "test_no", {"footnote", "source_table", "pdf_page"}),
                        ("table_7_1.csv", "test_number", {"footnote", "source_table", "pdf_page"}),
                        ("appendix_a_tests.csv", "test_no", {"table", "pi", "pdf_page", "flow_direction", "merged_grid_rows"})):
    rows = read(name); n = miss = 0; missed = []
    rowfail = 0
    for r in rows:
        cells = [v for k, v in r.items() if k not in skip and v]
        whole = sq("".join(cells))
        for k, v in r.items():
            if k in skip or not v or len(sq(v)) < 12: continue   # only long cells are meaningful per-cell
            n += 1
            if sq(v) not in txt:
                miss += 1; missed.append((r[key], k, v[:60]))
    print(f"{name}: {n} long cells compared with NTRS text, {miss} not found")
    for m in missed[:40]: print("   ", m)
