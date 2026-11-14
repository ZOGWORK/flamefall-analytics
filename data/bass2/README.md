# BASS-II test tables as CSV

Source: Olson et al., "Burning and Suppression of Solids–II (BASS-II) Summary Report", NASA/TM-20210011385 (2021), 144 PDF pages.
URL: https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf

Page numbers in every file are 1-based PDF page numbers (printed page number = PDF page − 8).
An empty cell means the source does not state the value. No value was typed by hand: every cell of the verbatim files is read from the PDF by script, and every label in the derived file carries a quote that a script checked against the source cell.

## Files and row counts

| file | rows | what it is |
|---|---|---|
| `table_2_1.csv` | 2 | Table 2.1, p36, verbatim |
| `table_4_1.csv` | 4 | Table 4.1, p55, verbatim (the two group rows "Black PMMA" / "Clear PMMA" became the `pmma_group` column) |
| `table_4_2.csv` | 2 | Table 4.2, p56, verbatim |
| `table_5_1.csv` | 20 | Table 5.1, p65, verbatim (M1–M20) |
| `table_7_1.csv` | 31 | Table 7.1, p104, verbatim (27 BASS-II rows + 4 BASS rows) |
| `table_d_2.csv` | 4 | Table D.2, p136, verbatim |
| `appendix_a_tests.csv` | 126 | Tables A.1–A.6, p111–121, one row per test, all 35 printed columns |
| `bass2_test_points.csv` | 290 | derived, one row per (test, flow condition) with an outcome label |

Appendix A rows per table: A.1 Bhattacharjee 22 (p111: 9, p112: 13); A.2 Ferkul 4 (p113); A.3 Fernandez-Pello 27 (p114: 15, p115: 12); A.4 Miller 20 (p116: 10, p117: 10); A.5 Olson 24 (p118: 14, p119: 10); A.6 T'ien 29 (p120: 17, p121: 12).
Cross-check on that count: p103 says "A total of 27 tests were carried out for the fabric samples in BASS–II"; A.6 has 29 rows, of which 2 (T3, T7) are the spherical section.

## How each file was produced

Scripts are in `scripts/bass2/`; `bash scripts/bass2/run_all.sh TM-20210011385.pdf` rebuilds every CSV here from the PDF (checked: byte-identical output).

1. `build_body_tables.py` → the six body-table CSVs. Cell boundaries come from the ruling lines (pdfplumber `find_tables`), the text of each cell from pymupdf spans (correct Unicode; superscript spans are separated, which is how footnote mark `b` in Table 7.1 is kept out of the O2 value and put in the `footnote` column). Printed headers are asserted in the script, so a layout change would stop the build.
2. `appx_cells.py` → `appx_logical.py` → `build_appendix_a.py` → `appendix_a_tests.csv`.
   - Stage 1 puts every pymupdf word of pages 111–121 into the pdfplumber grid cell that contains its centre (0 words left over on every page).
   - Stage 2 maps the 86–90 grid columns onto the 35 printed columns by horizontal overlap with the header cells.
   - Stage 3 starts a new test at every non-empty "Test number" cell and merges the following wrapped grid rows into it (18 tests had wrapped rows). Wrapped lines are joined with one space, or with nothing when the line ends in a hyphen or en dash (25 joins, e.g. `0.2-` + `mm PMMA` → `0.2-mm PMMA`, `self-` + `extinguished`; all listed in `build/bass2/appx_build_log.json`).
3. `build_test_points.py` + `points_spec.py` → `bass2_test_points.csv` (rules below).
4. `verify_against_text.py`, `verify_against_ntrs_txt.py`, `check_quotes.py` → the checks below.

### Checks run

- Every row of every verbatim file (not just 5 per table) was compared with `page.get_text()` of its page: the row's cells, concatenated in printed column order with whitespace removed, must occur in the whitespace-free page text. Result: 2/2, 4/4, 2/2, 4/4, 20/20, 31/31 for the body tables and 22/22, 4/4, 27/27, 20/20, 24/24, 29/29 for A.1–A.6. **0 mismatches.**
- Second source: all 469 Appendix A cells of 12+ characters (and the long cells of Tables 5.1 and 7.1) were searched in the NTRS full-text file. 0 not found.
- Rendered page images were read by eye against the CSV for: Tables 2.1, 4.1, 4.2, D.2 (whole), 5.1 (M1–M18), 7.1 (first 26 rows); A.1 B1 and B10–B17; A.2 F1–F4; A.3 P1–P13b and P22a–P24; A.4 M2–M5; A.5 O1–O12, O19–O2, O3a–O5b; A.6 T10–T18, T28a–T7. No mismatch. This matters for empty cells (e.g. the empty fan-display cells of T13, T14, T16–T18, T6, M2, M5), which the text check cannot see.
- The 35 report sentences and footnotes quoted in this README and in the derived file's basis notes were checked verbatim against the stated page (`check_quotes.py`).

## Appendix A column mapping (reversed header → meaning)

pdfplumber returns the rotated header text reversed; pymupdf returns it in reading order. Table A.4 (p116) shown; trailing letters are footnote marks.

| # | pdfplumber header text (reversed) | decoded header | CSV column |
|---|---|---|---|
| 1 | `,etad yalpsid oediv a)raeY rof( paeL etad rof lautcA 1 dda` | Actual date (for video display date, add 1 for Leap Year)a | `date` |
| 2 | `emit dne dna emit )emit trats etamixorppA yalpsid oediv(` | Approximate start time and end time (video display time) | `start_end_time` |
| 3 | `.rebmun tset nur-sA` | As-run test number. | `as_run_test_no` |
| 4 | `rebmun tseT` | Test number | `test_no` |
| 5 | `rebmun elpmaS` | Sample number | `sample_no` |
| 6 | `blairetaM` | Materialb | `material` |
| 7 | `retingI` | Igniter | `igniter` |
| 8 | `rotcirtser wolF` | Flow restrictor | `flow_restrictor` |
| 9 | `ecnatsid elpmaS` | Sample distance | `sample_distance_col_verbatim`, `flow_direction` |
| 10 | `cyalpsid naF` | Fan displayc | `fan_display` |
| 11 | `yalpsid riA` | Air display | `air_display` |
| 12 | `niag retemoidaR` + `)01 dna ;05 ;052 ;000,1(` | Radiometer gain (1,000; 250; 50; and 10) | `radiometer_gain` |
| 13 | `yalpsid retemoidaR` | Radiometer display | `radiometer_display` |
| 14 | `)2NG( negortin suoesaG` + `retemoitnetop` | Gaseous nitrogen (GN2) potentiometer | `gn2_pot` |
| 15 | `yalpsid 2NG` | GN2 display | `gn2_display` |
| 16 | `)N/Y( retliF` | Filter (Y/N) | `filter_yn` |
| 17 | `d)LC/HC( edom esaeleR` | Release mode (CH/CL)d | `release_mode` |
| 18 | `e)A/M( edoM erusopxE` | Exposure Mode (M/A)e | `exposure_mode` |
| 19 | `f)VE#–( noitasnepmoc erusopxE` | Exposure compensation (–#EV)f | `exposure_compensation` |
| 20 | `tekcarb erusopxe dna semarf tekcarB` + `g)0.1/F#(` | Bracket frames and exposure bracket (#F/1.0)g | `bracket_frames` |
| 21 | `s ,deeps rettuhS` | Shutter speed, s | `shutter_speed_s` |
| 22 | `pots F` | F stop | `f_stop` |
| 23 | `OSI` | ISO | `iso` |
| 24 | `h)tnoc/s( dloh rettuhS` | Shutter hold (s/cont)h | `shutter_hold` |
| 25 | `laires drac )DS( latigid eruceS` + `)N/S( rebmun` | Secure digital (SD) card serial number (S/N) | `sd_card_sn` |
| 26 | `tohs semarf latoT` | Total frames shot | `total_frames_shot` |
| 27 | `%lov ,2O laitini detarbilaC` | Calibrated initial O2, vol% | `o2_initial_cal_pct` |
| 28 | `%lov ,2O lanif detarbilaC` | Calibrated final O2, vol% | `o2_final_cal_pct` |
| 29 | `%lov ,2O laitinI` | Initial O2, vol% | `o2_initial_pct` |
| 30 | `%lov ,2O laniF` | Final O2, vol% | `o2_final_pct` |
| 31 | `%lov ,2OC laitinI` | Initial CO2, vol% | `co2_initial_pct` |
| 32 | `%lov ,2OC laniF` | Final CO2, vol% | `co2_final_pct` |
| 33 | `mpp ,OC laitinI` | Initial CO, ppm | `co_initial_ppm` |
| 34 | `mpp ,OC laniF` | Final CO, ppm | `co_final_ppm` |
| 35 | (not rotated) | Test observations and anomalies (ignited, spread, extinguished, burn time, color, etc.)c | `test_notes` |

The same 35 columns are on all 11 pages; only footnote letters and small wording change (A.1 says "GN2) pot" and has no comma before "vol%"; A.2 has no footnote on "Material" or "Fan display"; A.3 marks "Fan display" with b).
`appendix_a_tests.csv` holds the requested columns first, then the remaining printed columns, then `merged_grid_rows` (how many grid rows were merged into the test).

**Column 9 is headed "Sample distance" on every page, but its cells hold the flow direction**: Opposed 67, Concurrent 38, Stagnation 15, "?" 2 (O1, O2), "1" 4 (T1, T2, T4, T15, the four tests of 2/14/2014). `sample_distance_col_verbatim` keeps the cell as printed; `flow_direction` is filled only when the cell is one of the three direction words.

Footnotes under the tables: a Greenwich Mean Time; b "Polymethylmethacrylate (PMMA)." (A.1, A.4, A.5, on "Material") or "SIBAL is Solid Inflammability Boundary at Low Speeds." (A.6); "Potentiometer (pot)." on "Fan display" (A.3 p114 adds "Extinction (ext).", A.5 p119 adds "Maximum (max)."); the rest are camera abbreviations. Page 118 prints no footnotes (they are on p119).
Table 7.1 footnotes: a "Solid Inflammability Boundary at Low Speeds." (on the word SIBAL in the title); b "O2 reading in these two tests might be inaccurate." (on the O2 values of GMT45-T1 and GMT45-T2, stored in the `footnote` column).

## What "fan display" and "air display" mean

- **Fan display** is the fan-voltage readout of the video overlay, in tenths of a volt. p13: "The video camera had an overlay that displayed the N2 flow rate (cm3/min), fan voltage (10× V), air velocity transducer reading (cm/s), and the radiometer signal." p74: "The voltage to the fan was displayed and could be set."
  The column is not used consistently: many cells hold the fan **potentiometer** setting instead (footnote "Potentiometer (pot)."), or both, e.g. B10 `1.7 (52), 1.25, 0.9, 0.6, 0.4, 0.35`, O18 `57, 51, 47, 72, 51, 72, 51, 47 (2.3, 1.5, 1.0, 4.0, 1.5, 4.0, 1.5, 1.0)`. Values of about 40 and above are display readings; values from about 0.27 to 10 are pot settings.
- **Air display** is the reading of the air velocity transducer in cm/s (same p13 sentence). p12: "An omnidirectional spherical airspeed transducer (TSI Incorporated 8475) was positioned between the honeycomb and the screen and was used to measure the steady-state flow through the duct. The air velocity transducer probe had a response time of approximately 1 minute." p74: "its digital display only read out to the units place (no decimals) yielding an effective resolution of ±0.5 cm/s".
- **Flow restrictor** (0, 1 or 2 installed) changes the flow obtained at a given fan voltage. p12: "With no restrictors, the maximum flow velocity was ~55 cm/s, and with two restrictors this was reduced to ~35 cm/s."

**Does the report give a fan display → cm/s conversion? No.** It says a calibration existed and was redone daily, but prints neither a table nor an equation:
- p13: "The fan voltage was calibrated with the airspeed transducer at the end of every operations day."
- p74: "A fan calibration was performed at the end of each operational day to associate the fan voltage with the flow velocity for each flow restrictor, after the fan had adequate time for warmup."
- p29: "A hot wire anemometer is used to calibrate the flow velocity with fan voltage, which is used to determine the flow velocity."
- p21: "there are significant uncertainties in these values as the calibration at such low velocity has high error bars".

So no fan-display or pot value was converted. `flow_cm_s` is filled only from (a) the cm/s columns of Tables 5.1 and 7.1, (b) a cm/s value written in the test notes, or (c) the air-display cell, which is a cm/s reading by the p13 sentence. Single pairings that the report itself prints (e.g. "Fan pot 1.5 (5 cm/s)" in P5; Figure 3.1 caption, p54: "Postignition at 3 cm/s (potentiometer or pot 0.6)") are used only for that test.

The air display under-reads at the bottom of its range. Same tests, Table 7.1 flow vs Table A.6 air display: T4 `10 to 2.2` vs `9,1`; T13 `4 to 2.2` vs `5,1`; T6 `4.5 to 2.6` vs `5, 2, 1, <1`; T5 `10 to 2.4` vs `10, 2, 1`; T11 `4` vs `5`; T14 `4 to 2.8` vs `5, 3`. At 5 cm/s and above the two agree within about 1 cm/s (T9, T10, T12, T17, T19–T22). In the rod tables the air display reads 0 at pot settings where flames were burning. Column `flow_value_kind` says where each cm/s value came from (`body_table` 91 rows, `air_display` 68, `ops_notes` 31; 100 rows have no cm/s), and air-display values of 2 or less carry a caution in `notes`.

## bass2_test_points.csv

Columns are as requested, plus three at the end: `o2_final_pct`, `o2_final_basis`, `flow_value_kind`.
290 rows; 190 have `flow_cm_s`. Every Appendix A test appears at least once.

### Which source labels which test

- Miller M1–M20: Table 5.1 gives the sustained points (a spread rate at a velocity). Table A.4 adds only what Table 5.1 lacks: the extinction point of 16 tests, plus sustained rows for M16 ("1 cm/s or so") and M6 (two pot plateaus). Thickness, width and sides for all Miller rows come from Table 5.1.
- T'ien fabric tests: Table 7.1 gives flow, O2, width and the label. Table A.6 is used for the label only where the Table 7.1 comment is dashes and the A.6 note is clear (6 rows, `source_table` = "Table 7.1 + Table A.6"), and for T3 and T7, which are not in Table 7.1.
- Everything else: Appendix A (test notes first, air-display or fan-display cell where the notes are silent). The four pot-only rows of the candle test F4 rest on body text p54.

### Labelling rules as applied

- `sustained`: the source says the flame burned / spread / was steady / stayed lit / did not blow off at that condition; in Table 5.1, a spread rate at that velocity.
- Step tests: start flow = sustained when the test went on to a stated end outcome; end flow = quenched (flow reduced, or flow turned off) or blowoff (flow increased). Intermediate steps are emitted only when the step is listed in the row and either the notes name it (e.g. O15b "4 min 0.34") or it is a cm/s air-display step and the notes affirm steady burning in general (e.g. B10 "Multiple velocities for steady spread"). The `derivation` text says which.
- `no_ignition`: "did not ignite", "would not sustain", "would not stay lit", "no sustained flame", brief flames that go out.
- `ambiguous` (38 rows): dashes in Table 7.1 with no clear A.6 note (T1, T2, T5); footnote b on O2 (T1, T2); "Reused" samples in Table 7.1 (T23–T29); the four BASS rows (comment only says "BASS"); "Not tracked" spread rates (M6, M12 in Table 5.1); notes that describe a flame but no outcome (B2, B3, B4, B5, B7, B12, O1, O2, O3b); B14, P21b, P22b (see below).
- O2: `o2_pct` is the calibrated initial O2 for Appendix A rows, the "Initial O2" column for Table 5.1 rows (identical to A.4 calibrated initial for all 20 tests), and the single O2 column for Table 7.1 rows (identical to A.6 calibrated initial for all 27 BASS-II tests). The calibrated final O2 is given next to it because many extinction points happened after long burns.

### Outcome counts by PI (all 290 rows)

| PI | sustained | quenched | blowoff | no_ignition | ambiguous | total |
|---|---|---|---|---|---|---|
| Bhattacharjee | 31 | 9 | 2 | 0 | 7 | 49 |
| Ferkul | 5 | 1 | 0 | 3 | 0 | 9 |
| Fernandez-Pello | 36 | 22 | 0 | 3 | 3 | 64 |
| Miller | 42 | 16 | 0 | 0 | 4 | 62 |
| Olson | 28 | 10 | 8 | 6 | 3 | 55 |
| T'ien | 18 | 7 | 1 | 4 | 21 | 51 |
| all | 160 | 65 | 11 | 16 | 38 | 290 |

### Outcome counts by material_class

| material_class | sustained | quenched | blowoff | no_ignition | ambiguous | total |
|---|---|---|---|---|---|---|
| PMMA | 138 | 58 | 10 | 10 | 17 | 233 |
| SIBAL-cotton | 17 | 6 | 1 | 3 | 21 | 48 |
| Nomex | 0 | 0 | 0 | 3 | 0 | 3 |
| other: Japan Wax candle | 5 | 1 | 0 | 0 | 0 | 6 |
| all | 160 | 65 | 11 | 16 | 38 | 290 |

Only the 190 rows that have a cm/s value:

| material_class | sustained | quenched | blowoff | no_ignition | ambiguous | total |
|---|---|---|---|---|---|---|
| PMMA | 105 | 12 | 2 | 6 | 13 | 138 |
| SIBAL-cotton | 17 | 6 | 1 | 3 | 21 | 48 |
| Nomex | 0 | 0 | 0 | 3 | 0 | 3 |
| other: Japan Wax candle | 1 | 0 | 0 | 0 | 0 | 1 |
| all | 123 | 18 | 3 | 12 | 34 | 190 |

Most extinction points have no cm/s value because the source gives them as potentiometer settings (e.g. "extinguished at pot 0.35").

By source table: Table 5.1 43; Table 7.1 42; Table 7.1 + A.6 6; A.1 49; A.2 9 (4 of them with p54 text); A.3 64; A.4 19; A.5 55; A.6 3.

## Judgement calls and cells I was unsure about

Transcription

1. Column 9 header says "Sample distance" but holds flow direction (see above). T1, T2, T4, T15 show "1" there, O1 and O2 show "?"; their direction is not stated in Appendix A. For the Table 7.1 rows the direction "concurrent" comes from the table title.
2. Dates printed as `6/24/2018` (F4, T9, T10, T18) are kept as printed; Table 7.1 calls T9, T10, T18 "GMT175", which is 24 June 2014. O3b has an empty date cell.
3. Calibrated-final O2 cells that are not readings, kept as printed in `appendix_a_tests.csv`: B2 `1.6`, F3 `0.9`, P22a `0.6`, T28a `0.9`, P22b `39.1`, T28b `40.4`. In each case the raw initial or final O2 cell is dashes. B14 has dashes in all final cells. The derived file leaves `o2_final_pct` empty for these.
4. P22b calibrated initial O2 `20.0` is the only value printed in red in Appendix A, and its raw initial O2 is `----`. I treated that as "O2 not measured": both P22b points are labelled `ambiguous`, with the label they would otherwise have in `notes`.
5. M5: SD card cell `10,` + `14` → `10, 14`; total frames `300+` + `+102` → `300+ +102`. M5 material says "2 cm thick" (probably "wide"); kept as printed.
6. F1 material reads `Nomex® (DuPontTM) natural (Nomex III)`; "TM" is a superscript trademark sign in the PDF.
7. O13a and O5a/O5b have the two columns swapped in the source (pot settings in the fan-display cell, fan readings in the air-display cell with air readings in brackets). Kept as printed.
8. Table 4.2 prints the 0.009525 m flow range as `0.043 to 0.02` (high to low); kept.
9. Table D.2 belongs to BASS, not BASS-II: p135 says the four tests burned "Sample 19 (1-cm PMMA sphere)".
10. Table 5.1 has no footnotes; its `footnote` column is empty.

Units

11. Nothing was converted. Film thickness given in µm (B1–B5, B7, B12, B14, B16–B22) is left out of `thickness_or_diameter_mm`, with the µm text in `notes`; the 4 cm spherical section (T3, T7) likewise. Dividing by 1000 or multiplying by 10 would fill them.
12. Widths differ between tables for the same samples: Table 5.1 and 7.1 say 2.2 / 1.2 cm, Appendix A material text says 2 cm / 1 cm. Each row uses its own source table (Miller rows use Table 5.1).
13. T24: Table 7.1 gives width 2.2 cm, A.6 material says "1 cm SIBAL, top side ign". The Table 7.1 value is used; the row is ambiguous anyway (reused sample).

Labels

14. Cross-table labels (6 rows): T6 start and end, T16 start and end, T11, T19 take the flow from Table 7.1 and the outcome from the A.6 note ("still did not extinguish", "flame spread whole sample at 3 cm/s", "Burned completely, steady", "Steady burn"). Read strictly from Table 7.1 alone they would be ambiguous (dashes). Filter on `source_table` = "Table 7.1 + Table A.6" to revert.
15. T4 and T18 start-flow rows are `sustained` by the step rule ("10 to 2.2 … Quenched"), but the A.6 notes say the flame was short-lived: T4 "flow velocity changed immediately after ignition down to 1", T18 "Brief ignition but flame extinguished as it spread away from igniter". The A.6 note is copied into `notes` on every Table 7.1 row.
16. "Reused, did not ignite" (T23, T28a, T28b) and "Reused, ignited" rows are `ambiguous`, as instructed, although the comment words are clear. p103: "These reused samples in general had a short unburned length and provided less quantitative data".
17. Second burns of an already burned rod (P9, P13b, P21b, P22b, P25, P3b, O3b, O5b, O8b, O13b, O15b; also P8 and T7) are not downgraded for being reburns; the reburn is stated in `notes`. O15b's own note asks "rod heatup effect?".
18. Miller extinctions at a finite flow (M2, M3, M5, M9, M10, M11, M14, M15, M18, M19, M20) are labelled `quenched` although they happened at 5–18 cm/s, because p66 says "Quenching extinction data was also obtained at finite flow rates for most of the tests." M15's note writes "15" without a unit.
19. M9 has two rows at 14 cm/s: `sustained` from Table 5.1 (spread rate 0.025 mm/s) and `quenched` from A.4 ("died after 15 min at 14 cm/s"). Both are in the source; O2 fell from 18 to 17.6 between them.
20. M12: Table 5.1 lists velocities "12 and 10" (not tracked), while A.4 shows air display "<1" and fan 41–42. Left ambiguous.
21. Flow turned off or pot set to 0 is labelled `quenched` (B1, M1, M17, P2, P4, P5, P6, P13a). M1's was forced by the crew when the camera card ran out. P2 rests on "did not get extinction on stills, but was just fan off, not slow ramp".
22. P21a ("Flame self-extinguished at 5 cm/s") and O13b ("Only stayed lit at 0.9 for less than a minute") are labelled `quenched`: extinction at a constant low flow, not a blowoff attempt. O3a is `quenched` with no flow value ("probably overshot").
23. Listed-step rows (derivation starts "step test: listed step"): B10, B11, B13, B17, B20, P12 sustained rows use air-display steps under a general statement such as "Multiple velocities for steady spread"; P15 is the same kind of row with no end state. The lowest step of each (1 cm/s, or 0.5 for P12) is the least certain, and p21 puts the film extinction velocity at "about 1 cm/s" to "about 1.5 cm/s".
24. Start-flow rows that rest on the first air-display value without a note sentence naming it (e.g. P1, P14, P16, P19, P22a, O4, O10, O11) follow the step rule; p75 supports it for rods: "typically at a flow speed of 5 cm/s".
25. O17 and O18 blowoff rows take 11 cm/s from the air-display cell by position (fan 72 = pot 4.0 ↔ 11). O18's first blowout was recovered; the second was not. B15, B8, P19, O10 high-flow rows have no cm/s because the cell says only "max"/"maximum".
26. P14 "extinguished at 0.31", B9 "extinguished at 0.35", O4 "extinguished at 0.36", O6 "out 0.275": the number is taken to be a pot setting, the unit is not written. O6's label rests on the fan-display cell because its notes cell is dashes.
27. B14 is ambiguous: notes say "only brief ignition, flame extinguished" but the air display lists "5, 3, 2, extinction". P21b is ambiguous: the igniter broke.
28. F4 (candle): direction is "Stagnation" in Table A.2 but p54 says it "ignited in an opposed flow"; the table value is used. Sustained rows at pot 0.4, 0.35, 0.32, 0.31 rest on p54 text and the Figure 3.1 caption, not on the table.
29. Material class PMMA is not written in every material cell: A.3 rods rest on p55 ("rods of cast PMMA"), A.1/A.4/A.5 on the header footnote, the spherical section on p13. Nomex geometry is `other` because the report does not say what form the sample had.
30. The four BASS rows of Table 7.1 use `test_no` "BASS GMT96-T8" etc. so they cannot be confused with BASS-II tests T10 and T11.
