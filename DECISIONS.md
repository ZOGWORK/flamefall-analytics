# Decisions and corrections

Assumptions made while building, and every place where a number or statement in the research notes
or the build brief turned out to differ from its primary source. Each correction says what was
read and where.

## Corrections found by checking primary sources (14 Nov 2026)

C1 to C14 correct the research notes or the brief. C15 and C16 are inconsistencies inside the
sources themselves.

| # | Claim in the research notes or brief | What the primary source shows | What this project does |
|---|---|---|---|
| C1 | FLEX gas fractions "sum to 1.00 for all rows except FLEX-069, 075, 076, 079, 080, 081 (0.98)" | Table IX prints fractions to two decimals: 247 rows sum to 1.00, **22 rows to 0.99**, 6 rows to 0.98 and 1 row (FLEX-162) to 1.01. Confirmed cell by cell against the PDF | States the real distribution; `test_gas_fraction_sums` asserts it |
| C2 | "The BASS-II memo PDF returned HTTP 404; Tables 5.1, 7.1 and A.2 are unverified. Do not display row-level values" | The NTRS record's own metadata lists the file as `TM-20210011385.pdf`. That URL returns the 144-page memo; the 404 came from a guessed filename. Tables 2.1, 4.1, 4.2, 5.1, 7.1, D.2 and the six Appendix A test matrices were transcribed by script and every row checked against the page text (0 mismatches) | BASS-II rows are shown as verified and cite the memo's table and page. `data/bass2/`, `scripts/bass2/` |
| C3 | "26 PSI combustion investigations" | The PSI search for "combustion" returns 26 records, but 2 are not combustion science (PSI-181, a solder study; PSI-108, a fluid-physics experiment). 24 carry Research Area = Combustion Science | Shows "26 search results, 24 combustion science"; the two others are listed and never ranked |
| C4 | Saffire: "IV-1 SIBAL, peak HRR 3,150 W, 409 kJ" and "V-2 2,800 W" | In ICES-2024-365 Table 2 those are **average** heat release from fuel-consumption calorimetry. Peak heat release by oxygen-consumption calorimetry exists only for VI-2, VI-3 and VI-4 (3,217 / 3,080 / 1,507 W) | Two separate evidence rows, each with its method and "average" or "peak" in the text |
| C5 | "The 85% O2 figure belongs to Flame Design inverse flames, never to CFI-G" | PSI's own CFI-G inverse-flame table (PSI-159, 154 tests) has burner oxygen up to 0.85, and so does PSI's Flame Design inverse-flame table (PSI-10). The challenge page says the same: an oxygen-nitrogen mixture of up to 85% oxygen "flowed from the spherical burner creating an inside-out flame". Chamber-ambient oxygen in both normal-flame tables stops at 0.40 | The essential point stands and is enforced: 85% is a **burner feed, not an ambient**. It is attributed to the inverse flames of both investigations. `o2_is_ambient = False`; `test_inverse_flame_oxygen_is_a_burner_feed_not_an_ambient` |
| C6 | "LUCI has NO published quantitative results as of 14 Nov 2026. Do not present LUCI spread rates" | A conference presentation is on NTRS (20250010653, ASGSR, Dec 2025) with spread rates for both samples in simulated lunar gravity and in normal gravity, and chamber oxygen histories. Read in full | Recorded as the nearest real tests to partial gravity, labelled as preliminary slides, one flight, centrifuge-simulated gravity, not a PSI dataset. No limiting oxygen value is claimed, because the slides state none. See QUESTIONS.md Q3 |
| C7 | "There is NO Saffire VI-vs-IV spread-rate comparison in the literature. Do not present one" | ICES-2026-577 (NTRS 20260001992) Table 1 lists thin-fuel spread rates side by side: IV-1 3.6 mm/s, V-2 3.4 mm/s, VI-2 4.05 mm/s. Read in full | The three rates are shown together with their pressures and source. No ratio or trend is derived from them. See QUESTIONS.md Q3 |
| C8 | "CO/CO2 molar ratio 0.01 to 0.1" (ICES-2015-196) | The paper states no such range. It gives 550 ppm CO per 1% CO2 for concurrent rods and 370 ppm for thick slabs, about ten times efficient flue gas | The stated slopes are shown instead |
| C9 | "Buoyant velocities: 1 g 24 cm/s, lunar about 10 cm/s, Martian about 15 cm/s" | These come from ICES-2019-101, which could not be re-read (QUESTIONS.md Q2). A 2025 paper by the same group takes 35 cm/s as a high estimate for normal gravity and says the lunar value "is not known"; a 2004 paper expects more than 20 cm/s on the Moon and Mars | Recorded as disagreeing estimates. The 24 / 10 / 15 figures carry the verification level `unverified` |
| C10 | BASS-II "O2 13 to 22%"; rods "0.476 cm" and "0.318 cm" | The memo gives 13.6 to 22.2%, and those two figures are rod **radii** | Uses the memo's values |
| C11 | "PMMA concurrent rod minimum 13.6%" as the flammability-boundary minimum | Two separate verified numbers exist: 13.6% is the final oxygen reading of one quench test (and the figure on the 2014 poster, against a 16% normal-gravity limit); the memo's fitted boundary has its minimum at about 13.5%, against a 15.4% normal-gravity upward limit | Both are shown, each with its own source and comparison |
| C12 | PSI's FLEX experimental table would match Table IX row for row | PSI's table (PSI-69) has 274 rows numbered 1 to 274 in sequence. Aligned on the CIR identifier and time, all 274 rows match Table IX on every value except one documented cell (FLEX-114 pressure, printed as 0 by PSI and left empty here), but PSI's numbering stops agreeing with the FLEX test numbers after test 155, and FLEX-216 and FLEX-230 are absent | Table IX stays the authority for test numbers. `test_psi_flex_table_matches_table_ix_value_for_value` |
| C13 | "ACME operations Nov 2017 to Feb 2022"; "E-FIELD 14 Mar to Nov 2018" | Operations ran Sept 2017 to Feb 2022 with first science in Nov 2017; E-FIELD ran March to May and September to November 2018 (no day given) | Dates in the catalogue come from the PSI record; the E-FIELD statement uses the months only |
| C14 | "Three cool flames" in CFI-G | The press releases say three were first noticed on 23 June 2021. PSI's table marks 7 of 179 normal-flame tests as cool flames (5 on day 174 of 2021, 2 on day 291) | Both are shown, each attributed |

| C15 | The report's figure captions restate each test's atmosphere, so they could be quoted as evidence | 45 of the 268 captions that state an atmosphere differ from the report's own Table IX: 29 by 0.01 to 0.02, 16 by more (FLEX-185's caption sums to 1.47; FLEX-280's swaps nitrogen and helium). Table IX agrees with PSI's table on these tests | Table IX is the source of every value. The caption's wording is stored separately, never used as a value, and those 45 tests are flagged (`caption_atmosphere_differs`). `test_caption_atmosphere_is_recorded_but_never_used` |

| C16 | PSI experimental tables can be counted row by row | Three files repeat a block of rows exactly (8 rows in the CFI table, 34 in SPICE, 8 in E-FIELD Flames), and the CFI-G inverse-flame file carries 861 comma-only padding rows after its 154 tests | Blank rows are dropped on read; test counts and flame totals use distinct rows, and each count's source note says how many repeats were left out. `test_psi_tables_are_counted_without_padding_or_repeats` |

## Verified as stated

- `data/flex-table-ix.csv`: matches the source PDF on all 3,864 cells by an independent re-read
  (`scripts/verify_flex_table_ix.py`), and matches PSI's own table on all 274 rows PSI lists, apart from the one documented FLEX-114 cell.
- FLEX totals, ranges and missing-value counts in the brief: reproduced by `tests/test_flex.py`.
- SAME Table 1 and SAME-R Table 1 (all values), the detector-miss fractions, Saffire VI Table 1 and
  the 981 s alarm time, Saffire spread rates from the 2023 journal table, BRE (21% flames out within
  40 s; steady at 26.5, 34 and 40%; 1100 to 1200 K), the challenge page's atmosphere figures, the
  FM2 test matrix and carrier, SoFIE-GEL's envelope: all confirmed in full text. Read levels are
  recorded per statement in `data/evidence.json`.

## Going deeper than the research notes

- **Cool-flame evidence per test.** The report's Appendix B captions state, test by test, whether
  the authors saw evidence of cool-flame burning after the visible flame went out. Of the 60
  n-heptane tests logged as Extinction, 39 have cool-flame evidence, 8 have none, 6 are unclear and
  7 captions are silent. No methanol caption mentions a cool flame.
- **Droplet support and extinction wording** from the same captions (free-floating 210,
  fiber-supported 64; radiative 44, diffusive 39, undetermined between the two 4).
- **The official per-test tables.** PSI attaches an "Experimental table" CSV to 22 of the 26 records
  (25 files). All are copied into `data/psi/experimental_tables/` by `scripts/fetch_psi.py` and
  drive the catalogue's ranges.
- **290 BASS-II test points** with a stated outcome, 190 of them with a velocity in cm/s.
- **Open cool-flame kinetics** (six-step model, Williams and Nayagam 2019) and measured hot and
  cool burning rates for n-decane and n-octane.

## Design and modelling decisions

### Data
- **D1. Extra `extinction_mode` values.** Table IX records Disruption, and most captions do not say
  which extinction mode occurred. Four values were added rather than forcing rows into the four
  specified ones: `disruption`; `radiative_cool_flame_not_stated` (the caption says radiative and
  is silent on a cool flame); `radiative_no_cool_flame_evidence` (the caption says radiative and
  reports no evidence of a cool flame: FLEX-130, 266 and 267); `visible_extinction_mode_not_stated`.
- **D2. Schema rule (a)** is enforced in the checkable direction (no ignition means no K). Table IX
  prints no burning rate for 16 tests that did ignite; they are counted and left empty.
- **D3. Schema rule (b)** has one documented exception, FLEX-212 (cool-flame evidence in the
  caption, no diameters printed).
- **D4. Schema rule (c)** uses a 0.02 mm tolerance; FLEX-129 prints an extinction diameter 0.01 mm
  above its initial diameter.
- **D5. `D_rad_ext_mm` / `D_diff_ext_mm`** are filled only when the caption states that mode. The
  printed value is always kept in `visible_ext_diameter_mm`.
- **D6. Contact details removed.** PSI records carry investigators' e-mail addresses. Names and
  roles are kept; e-mail, phone, fax and address fields are stripped from the committed snapshot.
- **D7. PSI "investigation dates"** are the record's own start and end dates. For several records
  they are project dates, not on-orbit dates. They are shown as "record dates".
- **D8. BASS-II pressure** is taken as 1 atm for every test. The memo states it for the fabric
  tests; the other tests ran in the same glovebox working volume. This is an assumption, so every
  solid point carries `pressure_stated`: true where the source prints a pressure for that test (70
  points), false where it is assumed (242 BASS-II points, and the Saffire VI Nomex sample, which is
  given its campaign's initial pressure).
- **D9. Oxygen at the outcome.** Oxygen falls during a long burn in a sealed glovebox. A flame that
  quenched or blew off is placed at the end-of-test oxygen reading (which is what the memo plots on
  its flammability boundary); sustained and no-ignition points keep the initial reading.
- **D10. Nothing converted that the source does not convert.** The BASS-II appendix records many
  extinctions as fan potentiometer settings. The memo prints no conversion to cm/s, so 100 of 290
  points have no velocity and are not used in any model.

### Presentation rules
- **D11. "D² versus time" for a single test** is a d²-law line rebuilt from D0, average K and burn
  time. Table IX has no time series, so it is never called a measured trace. For 31 tests the
  printed K and burn time would take the line below zero, which a diameter squared cannot do; the
  line then stops at zero and `aggregates.d2_line` reports the time it gets there.
- **D12. Shares carry Wilson 95% intervals.**
- **D13. The end marker of that line** is called an extinction diameter only when the outcome is
  Extinction; 24 Disruption and 15 Completion rows also print a value in that column.
- **D14. Environment filter.** Tags are computed from each investigation's own tested ranges by a
  stated rule. Station: tested near 21% O2. Rover: tested at 30% O2 or more, or at 70.3 kPa or
  less. Lunar: the rover rule, or tested in partial gravity. Spacecraft: vehicle-scale burn or
  smoke detection. A planned investigation has no tested range, so only its gravity can tag it,
  and it earns no relevance to any scenario: every term reads "planned, not tested".
- **D14a. Relevance in still gas.** An investigation that ran in still gas only is a full match for
  a still-gas scenario, and the match fades to zero over 20 cm/s of flow, like any other range.
- **D14b. Nearest tests and missing values.** A test that does not state one of the compared
  quantities (FLEX-114 has no pressure, 12 FLEX tests no initial diameter, 100 solid points no flow
  speed) is compared on the quantities it does state, is ranked after every test that states them
  all, and says which quantity was not compared.
- **D15. Search is retrieval and extraction only.** TF-IDF over catalogue rows and sourced
  statements. The answer is the matching statements with their sources. No text is generated, so
  no number can be invented. An oxygen limit stated in the question is applied as a filter on the
  recorded ambient range, of statements and of investigations alike, and the filter is echoed back.
  A fuel class is applied only when the question's words point to one class; a question that names
  two ("which materials did the smoke detector miss") is answered by text match alone.
- **D16. The two SAME tables stay two tables,** never averaged.

### Triage score
- **D17. Formula and weights** are the research specification's. All weights and lookup values are
  design choices, stated as such.
- **D18. No renormalisation for solids.** The specification says the cool-flame weight is
  "renormalised over the remaining terms" for solids, but its own worked example (0.637 / 0.687 /
  0.337) does not renormalise. The worked example is followed, because the brief requires it as a
  unit test.
- **D19. Oxygen minimum** is 13.6% × 101 kPa for PMMA, as in the worked example, and 16.9% × 101.3
  kPa for SIBAL fabric (lowest oxygen with a flame in memo Table 7.1). Other materials use the PMMA
  value and are flagged.
- **D20. The formula disagrees with one real test.** By partial pressure
  the Saffire VI fabric burn (31% O2 at 54 kPa, 16.8 kPa of oxygen) scores zero on the oxygen term,
  yet the fabric burned. A limit measured at 1 atm does not transfer to low pressure by partial
  pressure alone.
- **D21. The gravity term** (lunar scored highest) follows the specification. The LUCI slides show
  slower spread in simulated lunar gravity for both samples, with a longer burn for the fabric. The
  term is a design choice, not a finding.

### Models
- **D22. Three models, never pooled:** droplet extinction, droplet cool-flame evidence, solid
  sustained burning.
- **D23. Droplet target.** The specification names "cool flame" as the droplet target. Table IX has
  no such column, and caption labels exist for 47 tests only. So the well-powered model predicts
  visible-flame extinction (275 rows), and the cool-flame model is fitted on the 47 labelled tests
  and marked exploratory.
- **D24. Grouping.** FLEX is one investigation, so its groups are the 46 tested atmospheres
  (composition plus nominal pressure). Solid groups are investigations, with BASS-II split into its
  six investigator test series. Groups under 5 rows are merged for splitting, for solids only.
- **D25. Features.** For droplets, flow, flow direction, gravity and their interactions are constant
  and dropped; CO2 and helium fractions are added, with the reason written in the model card.
- **D26. C is chosen on pooled inner out-of-fold log-loss,** which stays defined when a fold holds
  one class.
- **D27. Disruption** is never the positive class. A sensitivity run without Disruption rows is
  reported.
- **D28. The solid model fails and is reported as failing.** Grouped-CV AUC 0.48 (95% interval 0.38 to
  0.65). It is not used for any estimate. One pre-declared variant (flow also entered squared, for
  the two-branch boundary) was run once and did not help (0.50); it was not adopted.
- **D29. Stress test.** Leave-one-fuel-out for droplets, leave-one-material-out for solids. The
  headline is the worse of that and grouped CV: 0.74 for droplet extinction. Every cool-flame row
  is n-heptane, so that model has no stress test; its card says its headline is grouped CV alone.
- **D29a. One input is not an initial condition.** For a solid-fuel flame that went out, oxygen is
  the end-of-test reading (D9). That reading exists only because the flame went out, so the input
  is chosen with knowledge of the outcome. It moves 13 of the 179 rows, all not sustained. The
  card states it; the solid model fails either way and gives no estimate.
- **D30. Distance to data** is the nearest-neighbour distance in standardised input space, compared
  with the 95th percentile of the training rows' own nearest-neighbour distances, plus a per-input
  range check.

### Process
- **D31. Layers and stack.** Python owns the data: loading, checking, aggregating and fitting
  (pandas, numpy, scikit-learn; versions pinned to the ones the tests ran on). A front end is a
  separate layer that reads what Python exports and never re-derives a source value; none is part
  of this change. Models are trained offline and stored as JSON; an estimate is computed from the
  stored coefficients, never by re-fitting.
- **D32. Research agents.** Four background agents read sources in parallel and reported verbatim
  quotes with page and read level. LUCI, the 2026 Saffire table, the SoFIE-GEL table, the BASS-II
  poster and the lunar-gravity ignition paper were then re-read directly before use. Statements
  that rest on an agent's reading alone say "read by research agent" in their read level.
- **D33. One export, checked both ways.** `scripts/export_web.py` writes everything the web app
  reads. Where the app must answer at once (a filter, a slider) it repeats a calculation that
  lives in Python; the export also writes Python's answers for a fixed set of cases
  (`golden.json`), and the app's tests compare. The committed export is itself tested for being
  current.
- **D34. Tied scores keep corpus order.** Search results are sorted with a stable sort, so two
  statements with the same score always come back in the same order, in Python and in the browser.

