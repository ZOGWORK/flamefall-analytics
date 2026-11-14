# Human spot-checks

The Space Apps rules ask what was human-verified against primary sources. This is the list for a
team member to work through before submitting. Each line names the number as the dashboard shows
it, where it appears, and the exact place to look. Tick it, initial it, and note the date.

Nothing below has been ticked by a human yet.

| # | Number as shown | Where in the dashboard | Where to check | Checked by / date |
|---|---|---|---|---|
| 1 | FLEX-001: methanol, 757.7 mmHg, D0 1.69 mm, K 0.52 mm²/s, 4.3 s, Disruption | FLEX Explorer, table | NASA/TP-2015-216046, Table IX, PDF p. 26, first row: https://ntrs.nasa.gov/api/citations/20150023456/downloads/20150023456.pdf | |
| 2 | FLEX-280: heptane, 766.2 mmHg, 0.21/0.64/0/0.15, D0 2.82 mm, 11.7 s, Extinction | FLEX Explorer, table | Same report, Table IX, PDF p. 34, last row | |
| 3 | 276 rows; Extinction 186, Disruption 62, Completion 28 | Overview cards | Run `python -m pytest tests/test_flex.py` and read `test_outcome_totals` | |
| 4 | FLEX-196 caption: cool-flame burning "likely" after extinction | FLEX Explorer, single test | Same report, Appendix B, Figure 199 (the figure for test FLEX-196; figure and test numbers differ) | |
| 5 | Minimum of the PMMA rod flammability boundary about 13.5% O2, against 15.4% in normal gravity | Catalogue, BASS-II | NASA/TM-20210011385, report pp. 75-76: https://ntrs.nasa.gov/api/citations/20210011385/downloads/TM-20210011385.pdf | |
| 6 | SIBAL quenched at 2.2 cm/s, 18.7% O2 (GMT45-T4); blew off at 47 cm/s, 17.2% (GMT190-T21) | Catalogue, BASS-II; Scenario Lab nearest tests | Same memo, Table 7.1, report p. 96 | |
| 7 | Kapton smoke 80 nm fresh, 155 nm aged (first flight) | What We Don't Know, smoke | SAME Final Report, Table 1: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=904707 | |
| 8 | Kapton smoke 42 nm fresh, 89 nm aged (reflight) | What We Don't Know, smoke | AIAA 2012-3536, Table 1: https://ntrs.nasa.gov/citations/20130000422 | |
| 9 | Far-field detector reached 1 mg/m³ at 981 s in Saffire VI-3 | What We Don't Know; Catalogue, Saffire-VI | ICES-2024-365, p. 5: https://ntrs.nasa.gov/citations/20240002981 | |
| 10 | Saffire VI-2: 54.1 kPa, 31.0% O2; peak 3,217 W | Catalogue, Saffire-VI | Same paper, Tables 1 and 2 | |
| 11 | LUCI fabric: 0.92 mm/s in simulated lunar gravity against 1.5 mm/s | What We Don't Know, partial gravity | ASGSR 2025 slides 19 and 33: https://ntrs.nasa.gov/citations/20250010653 | |
| 12 | Burner oxygen up to 0.85 in inverse flames; chamber oxygen at most 0.40 | What We Don't Know; Catalogue, ACME-CFI-G | PSI-159 experimental tables: https://psi.nasa.gov/physci/repo/data/investigations/PSI-159 | |
| 13 | 26 search results, 24 combustion science | Catalogue cards | https://psi.nasa.gov/physci/repo/search?q=combustion | |
| 14 | Droplet model: grouped-CV AUC 0.88, 0.74 on an unseen fuel | Model Lab | Run `python scripts/train_models.py` and read the printed lines | |
