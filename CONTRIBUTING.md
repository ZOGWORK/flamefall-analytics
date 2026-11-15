# Contributing

This project reports what experiments measured. A change is welcome when it keeps that true. The
rules below are the main ones the tests and reviews hold every change to. The tests are the full
statement: `tests/test_wording.py` for wording, the others for the data and the models.

## Rules about the science

1. **Every number has a source.** A number shown to a reader comes from a data file, or is
   computed from one, and carries its report, table, page or test number. Do not type a number
   into a page.
2. **Missing stays missing.** An empty cell in a source is never filled, estimated or drawn as
   zero.
3. **Kinds of evidence are never pooled.** Droplet, gas-flame, solid-fuel and smoke results do not
   share a chart, an average or a model.
4. **Three outcomes stay three.** In the FLEX data, Extinction, Disruption and Completion are
   separate. A disruption is not an extinction.
5. **"No visible flame" is not "fire out".** Cool-flame burning after the visible flame goes out is
   always shown.
6. **No data means no data.** There is no partial-gravity combustion dataset in the repository. A
   question about lunar or Martian gravity gets that answer and the nearest real tests, never a
   scaled or modelled number. An experiment that is planned is listed as a plan, not as evidence.
7. **No verdicts.** Nothing is called acceptable, approved or the opposite. Outputs are
   measurements and estimates.
8. **An unverified statement says so,** and never feeds a model.
9. **Models are validated on groups they have not seen** (seed 42), use no outcome as an input,
   report the worse of their two scores, give the distance to the data with every estimate, and
   label any estimate outside the tested ranges.
10. **No single burning rate for n-heptane.** It moves with droplet size, oxygen and diluent, and
    the constants quoted for other fuels are not attached to it.
11. **85% oxygen is a burner feed.** It belongs to the inverse flames, is labelled as such, and is
    never put on an ambient-oxygen axis or matched by an ambient-oxygen filter.
12. **FM2 is planned.** It has no tested range and no launch date is given for it.
13. **The triage formula orders scenarios.** It is a stated design choice, not a risk rating, and
    its worked example is a unit test.
14. **No agency marks.** No NASA logo, insignia or mission patch, and nothing that presents the
    project as endorsed by NASA. The only image files are the app's icon and the two screenshots.
15. **Pages change in place.** Moving between pages or changing a filter never reloads the page.

If a test in `tests/test_wording.py` fails on your text, change the text.

## How to make a change

- Work on a branch and open a pull request. Nothing is pushed straight to `main`.
- One commit per file changed. The message starts with the file's path and says what changed, for
  example `flamefall/flex.py: count a caption that reports no cool flame separately`.
- Merge with a merge commit. Do not squash.
- If you change source data or anything in `flamefall/`, re-run the scripts that depend on it and
  commit their output. The order is in [scripts/README.md](scripts/README.md).
- Where the web app repeats a calculation that lives in Python, change both, and let the parity
  tests in `web/src/lib/__tests__/` compare them.
- New behaviour comes with a test that fails without it.

## Check your change

From the repository root, in the activated Python environment:

```bash
python -m pytest
python scripts/export_web.py --check
```

From `web/`:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

All of these must pass before a pull request is merged.

## Documents

Say only what is true of the repository at that commit. Do not describe a page or a feature that
is not there, and do not say something was reviewed or verified unless it was, and say by whom.
Decisions and corrections go in `DECISIONS.md`; anything that needs a person goes in
`QUESTIONS.md`.

## Licence

By contributing you agree that your contribution is released under the MIT licence in `LICENSE`.
