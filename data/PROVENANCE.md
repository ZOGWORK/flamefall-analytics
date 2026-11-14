# Data provenance

Every file in `data/` is listed here with where it came from and how to rebuild or re-check it.
Nothing in this folder is estimated, interpolated or imputed. An empty cell means the source prints
no value.

## `flex-table-ix.csv` — FLEX droplet-burn results (276 rows, 16 columns)

| | |
|---|---|
| Source report | *Detailed Results From the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011*, Dietrich et al., NASA/TP-2015-216046, November 2015 |
| Table | Table IX, "Results by test number and FLEX identifier", Appendix A.2, PDF pages 26–34 |
| NTRS record | https://ntrs.nasa.gov/citations/20150023456 |
| PDF | https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf (42,900,650 bytes, 314 pages, SHA-256 `b4f6ca983e2792c33a0b92220a791a818f426bb635b94f7fd33dc8c9c471e79d`) |
| PSI record | PSI-69 |
| Extraction | pdfplumber 0.11.10 table extraction (done before the build; the CSV was supplied to the build as an input) |
| Independent check | `scripts/verify_flex_table_ix.py`: PyMuPDF word positions, a different library and method. All 276 × 14 = 3,864 cells match (run 14 Nov 2026) |

This is the 2015 edition covering March 2009 to December 2011. The earlier edition
(NASA/TP-2013-216046) covers a shorter period and is not used.

The report is a primary source found by the builder. It is **not** one of the links on the
challenge's Resources tab.

### Columns

`test_no` (FLEX number without the prefix), `cir_id` (CIR engineering identifier), `date` (M/D/YY as
printed), `gmt`, `fuel`, `pressure_mmhg`, `o2`, `n2`, `co2`, `he` (ambient mole fractions as printed,
two decimals), `d0_mm` (droplet diameter at time zero), `extinction_diameter_mm` (visible-flame
extinction diameter), `burning_rate_mm2_s` (average burning-rate constant from a linear fit of D²
against time), `burn_time_s`, `outcome` (Extinction / Disruption / Completion), `notes` (cleaning
flags).

### Cleaning rules (all recorded in the `notes` column where they change a value)

| Row | Printed in the source | In the CSV | Why |
|---|---|---|---|
| any | `-` or `–` | empty | the source's own "no value" mark |
| any | `.21`, `.6` | `0.21`, `0.6` | leading zero added |
| FLEX-114 | pressure `0` mmHg | empty | physically impossible for this experiment (range 526.3–2319.9 mmHg) |
| FLEX-227 | burn time `~6` | `6`, flagged approximate | |
| FLEX-229 | burn time `~9` | `9`, flagged approximate | |
| FLEX-070, FLEX-073 | same CIR identifier `193F001`, same date and time | both kept, both flagged | separate FLEX numbers with different diameters and rates |
| FLEX-212 | D0, extinction diameter, burning rate and burn time all `-`; pressure (759.8 mmHg), gas fractions (0.16 / 0.84 / 0 / 0) and outcome (Extinction) are printed | those four cells empty, the rest as printed | kept as printed |
| FLEX-039, 043, 051, 052, 063, 069, 093, 135 | extinction diameter `0` | `0` | printed as zero, so kept as zero, not treated as missing. All eight ended in Disruption or Completion, none in Extinction |

The "visible flame extinction diameter" column is not empty for every test that did not
extinguish: 24 Disruption and 15 Completion rows print a value there (159 Extinction rows do).
`flamefall/aggregates.py` names that value an extinction diameter only when the outcome is
Extinction; for the other two outcomes it is the diameter printed at the end of the test.

### Recomputed facts (asserted by `tests/test_flex.py`, never hard-coded in the app)

- 276 rows, FLEX-001 to FLEX-280; numbers 156, 205, 213 and 228 do not appear in Table IX.
- Outcomes: Extinction 186, Disruption 62, Completion 28.
- Methanol 157 tests (126 Extinction, 80.3%); n-heptane 119 tests (60 Extinction, 50.4%).
- Ranges: pressure 526.3–2319.9 mmHg; O2 0.12–0.34; N2 0.09–0.88; CO2 0–0.70; He 0–0.45;
  D0 1.10–4.67 mm; extinction diameter 0–4.60 mm; burning rate 0.05–1.06 mm²/s; burn time 0.30–39.2 s.
- Missing: GMT 1, pressure 1, D0 12, extinction diameter 78, burning rate 16, burn time 6.
- Helium present in 51 tests, CO2 in 123, both together in 0.
- Gas fractions as printed sum to 1.00 in 247 rows, 0.99 in 22 rows, 0.98 in 6 rows
  (FLEX-069, 075, 076, 079, 080, 081) and 1.01 in 1 row (FLEX-162). The source prints two decimals;
  these are rounding in the source, confirmed by the independent PDF check.

## `flex_caption_annotations.csv` — what the report says about each test in prose (274 rows)

| | |
|---|---|
| Source | Same report, Appendix B: one figure per test, each with a descriptive caption |
| Text used | NTRS full-text file, https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.txt |
| Script | `scripts/extract_flex_captions.py` |

Table IX does not record cool flames, how the droplet was held, or whether an extinction was
radiative or diffusive. The captions do. For each caption the script keeps:

- `support`: free-floating (210) or fiber-supported (64), from the caption's first sentence.
- `cool_flame`: `indicated` (39), `not_indicated` (8), `unclear` (7), or empty when the caption says
  nothing (220). The exact sentence is kept in `cool_flame_quote`.
- `extinction_wording`: `radiative` (44), `diffusive` (39), `both_mentioned` (4), or empty (187).
  `both_mentioned` means the caption says it cannot tell which of the two it was (FLEX-247, 251,
  255, 264). A caption that states one mode and names the other as a contribution, such as
  FLEX-225 ("extinguished diffusively with a significant contribution from radiative loss"),
  takes the stated mode. A caption that offers a mode only as one of two alternatives (FLEX-140,
  FLEX-141: "either extinguished radiatively or was completely outside of the quasi-steady
  flammability boundary") states no mode and is left empty. All 87 labelled sentences were read
  one by one against these rules.

Reading rules, applied by phrase and then read row by row:

- "indicative of", "evidence of", "probably followed by", "likely" → `indicated`. These are the
  report authors' inference from continued vaporisation and a vapour cloud after the visible flame
  disappeared. FLEX had no direct cool-flame imaging. Two captions hedge further ("may be
  indicative", "may have been"): FLEX-079 and FLEX-217. They are kept as `indicated` and can be
  identified from the quote.
- "no evidence of", "probably no" → `not_indicated`.
- "not clear", "not known", "not enough evidence", "difficult to determine" → `unclear`.
- A silent caption stays empty. It is **not** treated as "no cool flame".

- `support_quote` holds only the opening words the support label rests on ("Free-floating
  methanol droplet").
- `caption_atmosphere` holds the atmosphere as the caption words it (268 of 274 captions state
  one). **It is never used as a value.** For 45 tests it differs from Table IX: 29 by 0.01
  to 0.02 in one or two gases (the caption gives a nominal mixture, the table the printed one), and
  16 by more, including plain slips such as FLEX-185 (caption 0.70/0.52/0.25 O2/N2/CO2,
  which sums to 1.47; table 0.23/0.52/0.25), FLEX-280 (nitrogen and helium swapped) and FLEX-158 to
  160 (the caption repeats the previous series' mixture). Table IX agrees with the repository's own
  table on these tests, so Table IX is used everywhere and the 45 tests are flagged
  (`caption_atmosphere_differs`). `flex.caption_atmosphere_conflicts()` lists them.

FLEX-149 and FLEX-240 have no caption in the full-text file and carry no annotation.

## `flex_droplets.csv` — normalised research schema (276 rows)

Built by `scripts/build_flex_droplets.py` from the two files above: the 24 schema columns in order,
followed by clearly separated extras. Columns the source does not give (cool-flame burning rate,
second-stage extinction diameter, flame temperatures, flame standoff ratio, soot volume fraction)
are empty. `o2_is_ambient` is `True` for every FLEX row: all FLEX oxygen values are chamber ambient.
See `DECISIONS.md` for where the schema had to be extended to avoid inventing a category.

## `psi/` — snapshot of the PSI Data Repository (the challenge's official data source)

| | |
|---|---|
| Source | PSI Data Repository, search term "combustion": https://psi.nasa.gov/physci/repo/search?q=combustion |
| Retrieved | 14 Nov 2026, through the public JSON endpoints the PSI web application itself calls |
| Script | `scripts/fetch_psi.py` (standard library only; endpoints listed in `psi/SNAPSHOT.json`) |
| Licence | PSI records state CC0-1.0 |

- `psi/search_combustion.json`: the 26 search hits in PSI's relevance order. 24 have Research Area
  "Combustion Science"; PSI-181 (Materials Science) and PSI-108 (Fluid Physics) do not.
- `psi/records/<id>.json`: each record's metadata as returned, minus two bulky version-diff fields
  (`added`, `removed`) and minus e-mail, phone, fax and address fields.
- `psi/files/<id>.json`: file counts and sizes per category for each record.
- `psi/experimental_tables/*.csv`: all 25 "Experimental table" files attached to those records,
  with their content unchanged (git may normalise line endings). 22 of the 26 records attach at
  least one.

Row counts need care. The CFI-G inverse-flame file has 861 comma-only padding rows after its 154
tests, and three files repeat a block of rows exactly (CFI 8 rows, SPICE 34, E-FIELD Flames 8). The
files are stored as published; `flamefall/psi.py` drops blank rows on read and counts distinct rows.

Text from the API contains U+FFFD characters where PSI's source had dashes or quotes. The files
keep PSI's bytes; `flamefall/psi.py::fix_text` repairs them for display only.

Cross-check against the core dataset: PSI's own FLEX table (PSI-69) lists 274 tests. Aligned on
CIR identifier and time, all 274 rows find their Table IX partner, and every value agrees except
one documented cell: PSI prints FLEX-114's pressure as 0, which this dataset leaves empty. PSI numbers its rows 1 to 274 in sequence rather than by FLEX
test number, and does not list FLEX-216 or FLEX-230 (`tests/test_psi.py`).

## `bass2/` — BASS-II test tables (126 tests, 290 labelled test points)

| | |
|---|---|
| Source | Olson et al., *Burning and Suppression of Solids-II (BASS-II) Summary Report*, NASA/TM-20210011385, October 2021 |
| NTRS record | https://ntrs.nasa.gov/citations/20210011385 |
| PDF | https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf (48,972,416 bytes, 144 pages, SHA-256 `5ffa911fd9b6356f204646003fb9342e341810dcdfdf5cb15756e7f01ec5f770`) |
| Scripts | `scripts/bass2/run_all.sh` rebuilds every CSV from the PDF; output checked byte-identical |
| Details | `bass2/README.md`: column mapping, labelling rules, checks, and 30 listed judgement calls |

Verbatim tables: 2.1, 4.1, 4.2, 5.1 (20 slab tests), 7.1 (31 fabric rows), D.2, and Appendix A
(126 tests, all 35 printed columns). Every row was compared with the text of its PDF page: 0
mismatches. `bass2_test_points.csv` is derived: one row per test and flow condition, labelled
sustained / quenched / blowoff / no_ignition / ambiguous, each label carrying the words it rests on.

The memo is a primary source found by the builder; it is not a link on the challenge's Resources tab.

## `solid_test_points.csv` — every solid-fuel test point with a stated outcome (313 rows)

Built by `scripts/build_solid_points.py` from `bass2/bass2_test_points.csv` plus 23 rows typed from
five sources, each named per row: the PSI-99 experimental table (Saffire-II, 10 rows), Olson et al.
2023 Table 1 (Saffire-I and -III, 2 rows), ICES-2024-365 Table 1 (Saffire-IV, -V and -VI, 5 rows),
ICES-2025-156 Table 1 (the Saffire-VI Nomex sample, 1 row) and NTRS 20240007628 Table 1 (SoFIE-GEL,
5 rows). 179 rows have oxygen, pressure, a velocity in cm/s and an unambiguous outcome.

## `evidence.json` — 66 sourced statements

One entry per quantitative statement outside the FLEX table: the statement, its value and
unit, conditions, `o2_is_ambient`, the source reference and URL, a verification level, the read
level (full text, accepted manuscript, slides, abstract only, or "read by research agent"), and a
short quote. `unverified` entries are marked as such wherever they appear and never feed a
model.

## `investigations.csv` and `investigations_curated.json` — the catalogue (33 rows)

Built by `scripts/build_investigations.py`. PSI-stated cells are copied from `psi/records/`; ranges
are computed from PSI experimental tables and say which table and column in `range_source`; the key
result points at an `evidence.json` entry. A cell that PSI does not state, and that no cited source
states, is empty. 26 rows are the PSI search hits; 7 are investigations the search does not return
(Saffire IV to VI, SoFIE-GEL, FLARE, LUCI, FM2) and are marked as such.

## `models/*.json` and `cv_splits.json`

Written by `scripts/train_models.py` (seed 42): coefficients, preprocessing statistics, every
validation metric, out-of-fold predictions, 1,000 bootstrap coefficient sets, and the exact fold
membership of every row. The cards are strict JSON: a missing value is `null`, never `NaN`.
