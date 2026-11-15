# Contributing

This project reports what experiments measured. A change is welcome when it keeps that true. The
rules below are the ones the tests and reviews hold every change to.

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
9. **Models are validated on groups they have not seen** (seed 42), report the worse of their two
   scores, and label any estimate outside the tested ranges.

The wording rules are checked by `tests/test_wording.py`. If a test there fails on your text,
change the text.

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
