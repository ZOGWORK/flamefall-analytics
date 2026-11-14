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

The app reads only the JSON in `src/data/` and `public/psi/`. Those files are written by
`python scripts/export_web.py` in the repository root and are committed; do not edit them by hand.
