# Flamefall Analytics: the web app

Next.js (App Router) with shadcn/ui, Recharts, Motion and react-countup. It is exported as a static site:
every route is prerendered, and moving between pages or changing a filter happens in the browser
with no page reload.

```bash
npm ci
npm run dev        # http://localhost:3000
npm run test       # compares the browser-side calculations with the Python reference answers
npm run lint
npm run build      # writes the static site to out/
```

Two scripts drive a real browser against a built copy of the site. They need Chrome (set
`CHROME_PATH` if it is not in the default Windows location) and the built site served locally:

```bash
node scripts/behave.mjs http://localhost:3211     # controls, shared links, in-place navigation, the deck's words; fails on error
node scripts/measure.mjs http://localhost:3211    # load, idle, scrolling and slider cost per page
```

The app reads only the JSON in `src/data/` and `public/psi/`. Those files are written by
`python scripts/export_web.py` in the repository root and are committed; do not edit them by hand.
The page at `/deck/` has no slide text of its own: `src/data/deck.json` holds the text of every slide
of the PowerPoint file, and a change to a slide is made in `scripts/build_deck.py`.
