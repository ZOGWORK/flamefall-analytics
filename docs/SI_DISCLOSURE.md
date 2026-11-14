# Use of SI (super intelligence) tools

Draft for the "Use of SI" field of the project page. Team Flamefall Analytics, Space Apps 2026,
challenge *Flame in Freefall*.

## Short version (paste into the project page)

SI tools were used throughout, and are disclosed in full in the repository
(`docs/SI_DISCLOSURE.md`).

- **Research notes.** An SI research assistant compiled the initial research notes from public
  sources before the build.
- **Code, data pipeline, web console and slide deck.** Written with Claude Code (Anthropic, model
  Claude Fable 5.2) acting as an SI coding agent, directed by the team. It also ran background SI
  research agents that re-read primary sources and recorded verbatim quotes.
- **Code review.** Loopy, an SI code-review bot, reviewed the first four pull requests over
  several rounds and its findings were fixed. It stopped on 14 Nov, when the organisation's monthly
  review allowance ran out, before any pull request reached its top score; it did not review the
  final code. After that the pull requests were self-reviewed by the SI coding agent, in passes.
  First, four fresh reviewer agents per pull request, given only the code and the project's rules,
  looked for rule violations and bugs in the code as it was first written. Then further fresh
  agents read each round of corrections, until a pass on the latest corrections found nothing
  above a minor point. Every finding was fixed or is listed with the reason it was kept
  (`DECISIONS.md` D42). The reviewer agents are the same model as the coding agent. That is SI
  checking SI-written code. It is not a human review.
- **Inside the console there is no generative model.** "SI-powered" means three auditable
  things: retrieval and extraction over sourced statements (TF-IDF search, no generated text),
  ranking by a stated formula with visible weights, and small logistic-regression models validated
  by grouped cross-validation. The console cannot produce a number that is not in a data file.
- **No SI-generated images, video or audio** are used. Charts are drawn from the data by code.
- **Verification.** The SI coding agent checked numbers against primary sources with scripts
  anyone can re-run: the core dataset cell by cell with two independent parsers and against the
  repository's own table; the solid-fuel tables row by row against the page text; literature
  values against the cited table or page, with the read level recorded per statement. Not every
  number is verified. Two statements rest on an abstract only and four could not be re-read; each
  is marked as such where it is shown. One heat-release figure in the triage formula comes from a
  paper that could not be re-read, and the pressure of most BASS-II tests is assumed, not printed;
  both are labelled. Fourteen statements in the research notes were corrected as a result of the
  checks (`DECISIONS.md`). Spot-checks by a person are a separate list with its own status:
  `docs/HUMAN_VERIFICATION.md`.

## Full disclosure

### Tools and what each produced

| Tool | Kind | What it produced | Where |
|---|---|---|---|
| SI research assistant (named "Bruno" in the team's notes) | Research and summarisation | The research notes and build brief used as the starting point: challenge brief summary, source list, initial values, proposed schemas, model protocol and ranking formula | Not in the repository; its claims are checked in `DECISIONS.md` |
| Claude Code, model Claude Fable 5.2 (Anthropic) | Code generation, data extraction, analysis, writing | All code in `flamefall/`, `scripts/`, `tests/` and `web/`; the data files derived from primary sources; documentation; the slide deck | Whole repository |
| Background research agents (same model) | Source reading | Verbatim quotes, pages and read levels for literature values; the PSI repository snapshot; the BASS-II table transcription | `data/evidence.json` (read level per statement), `data/psi/`, `data/bass2/` |
| Loopy (`loopyreviews-bot`) | SI code review | Review findings on the first four pull requests, until its monthly allowance ran out on 14 Nov. It did not review the final code | Pull-request threads |
| Reviewer agents (same model as the coding agent) | SI code review | Self-review of each pull request in passes (the code as first written, then each round of corrections): rule violations and bugs, each fixed or listed with the reason it was kept | `DECISIONS.md` D42 |
| scikit-learn logistic regression | Statistical model | Three small classifiers and their validation metrics | `data/models/`, Model Lab page |
| TF-IDF retrieval (scikit-learn) | Search | Ranking of sourced statements against a question | Catalogue page |

### What is not SI-generated

- **The data.** Every measured value comes from a public source: NASA/TP-2015-216046 (FLEX),
  NASA/TM-20210011385 (BASS-II), the PSI Data Repository records and experimental tables, and the
  papers cited per statement. No value was generated, estimated or interpolated by an SI tool.
- **Images.** There are none other than charts computed from the data.

### How SI output was checked against primary sources

| What | Check | Result |
|---|---|---|
| FLEX Table IX (276 tests, the core dataset) | Re-read from the PDF with a second library and compared cell by cell; then compared with the repository's own FLEX table | 3,864 of 3,864 cells match; 274 of 274 repository rows match |
| FLEX cool-flame, support and extinction labels | Rule-based extraction from the report's captions, each label stored with its sentence; all labelled sentences then read one by one | 54 cool-flame statements and 87 extinction statements read |
| BASS-II tables (126 tests) | Every transcribed row compared with the text of its PDF page; long cells also found in the NTRS full text; pipeline re-run from the PDF | 0 mismatches; output byte-identical on re-run |
| PSI catalogue | Pulled from the repository's public endpoints and stored unedited (contact details removed) | 26 records, 25 tables |
| Literature values (66 statements) | Each traced to a table, page or slide; a verbatim quote and the read level stored | 60 verified in full text, 2 abstract-only, 4 not re-read and marked "not verified" |
| Code | Automated tests, including the acceptance behaviours | More than 100 tests; run `python -m pytest` for the current count |

### Limits of that checking

The checks above were run by the SI coding agent, with scripts that anyone can re-run. They are
machine checks against primary sources, not independent human review. The same holds for the code
review after the bot stopped: it was done by SI reviewer agents of the same model as the coding
agent, not by a person and not by the review bot. The team's own spot-checks
are recorded separately in `docs/HUMAN_VERIFICATION.md`.
