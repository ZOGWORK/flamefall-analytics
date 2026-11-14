# Decisions and corrections

Assumptions made while building, and every place where a number in the research notes turned out
to differ from its primary source. Newest entries at the bottom of each section.

## Corrections to the research notes (checked against primary sources, 14 Nov 2026)

| # | Claim in the research notes | What the primary source shows | Action |
|---|---|---|---|
| C1 | FLEX gas fractions "sum to 1.00 for all rows except FLEX-069, 075, 076, 079, 080, 081 (0.98)" | Table IX prints fractions to two decimals: 247 rows sum to 1.00, **22 rows to 0.99**, 6 rows to 0.98 and 1 row (FLEX-162) to 1.01. Confirmed cell by cell against the PDF | The real distribution is recorded here and in `data/PROVENANCE.md`; `tests/test_flex.py::test_gas_fraction_sums` asserts it |
| C2 | "The BASS-II memo PDF returned HTTP 404; Tables 5.1, 7.1 and A.2 are unverified" | The NTRS record's own metadata (`/api/citations/20210011385`) lists the file as `TM-20210011385.pdf`. `https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf` returns the 144-page memo, and `.../TM-20210011385.pdf.txt` its full text. The 404 came from a guessed filename | Tables are being transcribed from the memo itself; solid-fuel rows will cite the memo's table and page. Lands with the catalogue |
| C3 | "26 PSI combustion investigations" | The PSI search for "combustion" returns 26 records, but 2 are not combustion science (PSI-181, a solder study; PSI-108, a fluid-physics experiment). 24 carry Research Area = Combustion Science | Catalogue will show "26 search results, 24 in Combustion Science" |
| C4 | Saffire table: "IV-1 SIBAL ... peak HRR 3,150 W, 409 kJ" (and V-2 2,800 W) | In ICES-2024-365 Table 2 those are **average** heat release from fuel-consumption calorimetry. Peak heat release by O2-consumption calorimetry exists only for VI-2, VI-3 and VI-4 (3,217 / 3,080 / 1,507 W) | Each Saffire number will carry its real column label and method. Lands with the catalogue |

## Verified as stated

- `data/flex-table-ix.csv` against the source PDF: an independent re-read with a different library
  (`scripts/verify_flex_table_ix.py`, PyMuPDF word positions) matches all 3,864 cells.
- FLEX totals, ranges and missing-value counts in the build brief: all reproduced by
  `tests/test_flex.py` from the CSV.

## Going deeper than the research notes

- **Cool-flame evidence per test.** The notes treat cool flames as a general FLEX finding. The
  report's Appendix B captions state, test by test, whether the authors saw evidence of cool-flame
  burning after the visible flame went out. `scripts/extract_flex_captions.py` turns those
  sentences into labels and keeps each quote. Result: of the 60 n-heptane tests logged as
  Extinction, 39 have cool-flame evidence, 8 have none, 6 are unclear and 7 captions are silent.
  No methanol caption mentions a cool flame.
- **Droplet support and extinction wording** come from the same captions (free-floating 210,
  fiber-supported 64; radiative 44, diffusive 39, undetermined between the two 4).

## Design and modelling decisions

- **D1. Schema: extra `extinction_mode` values.** The research schema allows
  `radiative_then_diffusive`, `diffusive_only`, `no_extinction_burnout`, `no_ignition`. Table IX
  also records Disruption, and most captions do not say which extinction mode occurred. Forcing
  those rows into the four values would invent information, so four values were added:
  `disruption`; `radiative_cool_flame_not_stated` (the caption says radiative and is silent on a
  cool flame); `radiative_no_cool_flame_evidence` (the caption says radiative and says there was
  no evidence of a cool flame: FLEX-130, 266 and 267); `visible_extinction_mode_not_stated`.
- **D2. Schema rule (a)** says the hot-flame burning rate is empty *if and only if* the test did not
  ignite. Table IX prints no burning rate for 16 tests that did ignite. The rule is enforced in the
  direction that can be checked (no ignition means no K); the 16 gaps are counted and left empty.
- **D3. Schema rule (b)** has one documented exception, FLEX-212: its caption reports probable
  cool-flame burning but Table IX prints no diameters for it.
- **D4. Schema rule (c)** uses a 0.02 mm tolerance. FLEX-129 prints an extinction diameter 0.01 mm
  above its initial diameter (3.34 vs 3.33 mm), which is the table's rounding step.
- **D5. `D_rad_ext_mm` / `D_diff_ext_mm`.** Table IX gives one "visible flame extinction diameter".
  It is copied to `D_rad_ext_mm` only when the caption states radiative extinction or cool-flame
  evidence, to `D_diff_ext_mm` only when the caption states diffusive extinction, and is always
  kept in the extra column `visible_ext_diameter_mm`.
- **D6. Layers.** Python owns the data: loading, checking, aggregating and (later) fitting. The
  front end is a separate React app that reads what Python exports and never re-derives a source
  value. This part of the repository is the Python layer only.
- **D7. "D² versus time" for a single test** is a d²-law line rebuilt from three printed numbers
  (D0, average K, burn time). Table IX has no time series. `aggregates.d2_line` returns the two
  ends of that line and names the end marker by outcome; it is never called a measured trace.
  For 31 tests the printed K and burn time would take the line below zero, which a diameter
  squared cannot do; the line then stops at zero and the function reports the time it gets there.
- **D8. Shares are shown with Wilson 95% intervals** so a share from 3 tests cannot be mistaken for
  one from 30.
- **D9. Stack.** pandas and numpy for the data layer, scikit-learn for fitting; versions pinned in
  `requirements.txt` to the ones the tests ran on.
