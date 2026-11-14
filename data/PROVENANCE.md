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
The dashboard calls that value an extinction diameter only when the outcome is Extinction; for the
other two outcomes it is shown as the diameter printed at the end of the test.

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
- `extinction_wording`: `radiative` (46), `diffusive` (39), `both_mentioned` (4), or empty (185).
  `both_mentioned` means the caption says it cannot tell which of the two it was (FLEX-247, 251,
  255, 264). A caption that states one mode and names the other as a contribution, such as
  FLEX-225 ("extinguished diffusively with a significant contribution from radiative loss"),
  takes the stated mode.

Reading rules, applied by phrase and then read row by row:

- "indicative of", "evidence of", "probably followed by", "likely" → `indicated`. These are the
  report authors' inference from continued vaporisation and a vapour cloud after the visible flame
  disappeared. FLEX had no direct cool-flame imaging. Two captions hedge further ("may be
  indicative", "may have been"): FLEX-079 and FLEX-217. They are kept as `indicated` and can be
  identified from the quote.
- "no evidence of", "probably no" → `not_indicated`.
- "not clear", "not known", "not enough evidence", "difficult to determine" → `unclear`.
- A silent caption stays empty. It is **not** treated as "no cool flame".

FLEX-149 and FLEX-240 have no caption in the full-text file and carry no annotation.

## `flex_droplets.csv` — normalised research schema (276 rows)

Built by `scripts/build_flex_droplets.py` from the two files above: the 24 schema columns in order,
followed by clearly separated extras. Columns the source does not give (cool-flame burning rate,
second-stage extinction diameter, flame temperatures, flame standoff ratio, soot volume fraction)
are empty. `o2_is_ambient` is `True` for every FLEX row: all FLEX oxygen values are chamber ambient.
See `DECISIONS.md` for where the schema had to be extended to avoid inventing a category.
