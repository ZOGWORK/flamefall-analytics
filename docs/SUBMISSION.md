# Submission pack

Everything to paste into the team project page on spaceappschallenge.org, and the checklist to run
before clicking **Submit for Judging**. Submission closes Sunday 15 November 2026, 11:59 PM local.

## Links

| Field | Value |
|---|---|
| Live project | https://flamefall-analytics.onrender.com |
| Demo (7 slides, public, no sign-in) | https://flamefall-analytics.onrender.com/deck/ |
| Code and data | https://github.com/ZOGWORK/flamefall-analytics |

## Project name

Flamefall Analytics

## High-level summary (short)

Decades of microgravity fire experiments are hard to find, compare and trust. Flamefall Analytics
is a web console that summarises, ranks and interprets them for people designing crewed spacecraft,
stations, lunar bases and pressurised rovers. It holds to three rules: every number carries its
source down to the table and test number; where nobody ran the test it says "no data" and shows
the nearest real tests; and it gives estimates with their uncertainty, never a verdict. Its core is
276 droplet-burn tests, 313 solid-material test points and 66 sourced statements. The two datasets
were checked against their primary sources cell by cell and row by row; of the 66 statements, 60
were verified in full text, and the six that could not be are shown greyed with the reason.
Checking changed fourteen statements in our own research notes, and the console shows where its
own model fails.

## Project details

**What it does.** Six pages. *FLEX Explorer*: all 276 droplet burns, filterable by fuel, oxygen,
pressure, diluent and outcome, with extinction share by gas level, burning rate, and a per-row
source. *Investigation Catalogue*: every combustion investigation the repository returns, with
objective, materials, conditions, key finding and record link; a search that answers with the
measured statements themselves; and ranking against a scenario by a stated rule. *Scenario Lab*:
set oxygen, pressure, ventilation flow, material and gravity; get the nearest real tests, a model
estimate where a validated model exists, and an explicit "no data" panel otherwise. *Model Lab*:
grouped cross-validation results, confusion matrices, calibration, what moved the prediction, and
a distance-to-data warning. *What We Don't Know*: partial gravity, solids above the tested oxygen
range, CO2 with helium, and three kinds of burning a crew cannot see. *Overview*: the headline
numbers.

**What we found by going back to the sources.**

- In 39 of the 60 n-heptane tests logged as "Extinction", the report's own captions describe
  evidence that the droplet kept burning as a cool flame after the visible flame was gone. "No
  visible flame" is not "fire out".
- Methanol droplets went out in 80.3% of tests and n-heptane in 50.4% in the same apparatus: fuel
  chemistry matters as much as atmosphere.
- The solid-material memo that our notes listed as unobtainable is on NTRS under its real file
  name. We transcribed 126 tests from it and checked every row against the page.
- "85% oxygen" in the repository is the burner feed of inside-out flames, not a cabin atmosphere.
  Chamber oxygen never exceeded 40%.
- No lunar- or Martian-gravity combustion dataset is in the repository. The nearest real evidence
  is one suborbital flight's preliminary slides, shown with that label.
- A model for solid materials, built exactly as specified, does no better than chance on test
  series it has not seen (AUC 0.48). We report that and do not use it.

**How SI is used inside the console.** Retrieval and extraction over sourced statements (no
generated text), ranking by a written formula with adjustable weights, and small logistic models
tested on groups of tests they never saw: AUC 0.88 on unseen atmospheres and 0.74 on an unseen
fuel for droplet extinction.

**Benefits.** A reviewer can click from any number to its table. A designer can see at once
whether a planned atmosphere was ever tested. A student can see how a model is validated honestly,
including one that fails.

**Tools.** Next.js (React, App Router), shadcn/ui, Recharts, Framer Motion, TypeScript and Vitest for
the web app, hosted on Render as a static site; Python, pandas, scikit-learn and pytest for the
data and models, run at build time only.

## NASA data and resources (used and linked)

- PSI Data Repository, combustion science (the data source named on the challenge page):
  https://psi.nasa.gov/physci/repo/search?q=combustion. 26 records and 25 experimental tables.
- NASA Combustion Science: https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/
- Found by the team, not provided on the challenge's Resources tab:
  - Dietrich et al., NASA/TP-2015-216046 (FLEX): https://ntrs.nasa.gov/citations/20150023456
  - Olson et al., NASA/TM-20210011385 (BASS-II): https://ntrs.nasa.gov/citations/20210011385
  - Urban et al., ICES-2024-365 and ICES-2026-577 (Saffire): https://ntrs.nasa.gov/citations/20240002981, https://ntrs.nasa.gov/citations/20260001992
  - Urban et al., AIAA 2012-3536 (SAME-R): https://ntrs.nasa.gov/citations/20130000422
  - Ferkul et al., ASGSR 2025 (LUCI): https://ntrs.nasa.gov/citations/20250010653

## Space agency partner and other data

- Urban et al., SAME Final Report (NIST): https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=904707
- Further papers are cited per statement in `data/evidence.json`.

## Use of SI

Paste the "Short version" from [SI_DISCLOSURE.md](SI_DISCLOSURE.md). The full table is in that file.

## Checklist before clicking "Submit for Judging"

- [ ] Open the live link in a signed-out (private) browser window: all six pages load.
- [ ] Open the deck link in a signed-out window: seven slides, arrow keys work.
- [ ] Project page has: live link, repository link, the data sources above, and the SI disclosure.
- [ ] At least one NASA data source is linked (PSI and the two NTRS reports are).
- [ ] The repository is public and carries the MIT licence.
- [ ] No NASA logo, flag, insignia or mission patch anywhere (none is used; `tests/test_wording.py` and `tests/test_deck.py` check).
- [ ] Human spot-checks in [HUMAN_VERIFICATION.md](HUMAN_VERIFICATION.md) ticked.
- [ ] Open questions in [../QUESTIONS.md](../QUESTIONS.md) answered, in particular team size (Q1).
- [ ] Click **Submit for Judging**.
