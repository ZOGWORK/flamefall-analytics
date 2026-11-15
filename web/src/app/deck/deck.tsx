"use client";

// The seven slides of the PowerPoint file, in the browser. The text, numbers and colours of every slide are
// read from deck.json, which scripts/build_deck.py writes from the slides themselves. What this file types
// is the shell around them, the three outcome names in the legends, the axis units and the labels for
// screen readers.

import { AnimatePresence, motion } from "motion/react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";

import { Kicker, OUTCOME_COLOR, Prose } from "@/components/console/primitives";
import { REPO_URL } from "@/components/shell/nav";
import { Button } from "@/components/ui/button";
import deck from "@/data/deck.json";
import type { Outcome } from "@/lib/types";

const S = deck.slides;
const D = deck.draw;
const OUTCOMES: Outcome[] = ["Extinction", "Disruption", "Completion"];

const TEXT_TONE: Record<string, string> = { amber: "text-amber", data: "text-data", ext: "text-ext", dim: "text-dim" };
const FILL_TONE: Record<string, string> = { amber: "var(--amber)", data: "var(--data)", ext: "var(--ext)", dim: "var(--dim)" };
/** The colour class of a named piece of a slide: its accent colour in the PowerPoint file, or plain text. */
const tone = (tones: Record<string, string>, name: string) => TEXT_TONE[tones[name]] ?? "text-foreground";

const HUGE = "text-[clamp(5rem,15vw,11.5rem)]";
const BIG = "text-[clamp(4.25rem,11vw,8.5rem)]";
const MID = "text-[clamp(3.25rem,8vw,6.25rem)]";
const SMALL = "text-[clamp(2rem,4vw,2.75rem)]";
const LINE = "max-w-xl text-[clamp(0.95rem,1.25vw,1.125rem)] leading-snug text-muted-foreground";
const TITLE = "font-heading mt-4 max-w-5xl text-[clamp(1.5rem,3.2vw,2.4rem)] leading-[1.12] font-bold text-foreground";

function Foot({ children }: { children: string }) {
  return (
    <p className="mt-auto pt-6 text-note text-muted-foreground">
      <span className="text-dim">Source: </span>
      <Prose text={children} />
    </p>
  );
}

function Hero({ value, caption, className, size = BIG }: { value: string; caption: string; className: string; size?: string }) {
  return (
    <div>
      <p className={`num leading-[0.95] font-bold whitespace-nowrap ${size} ${className}`}>{value}</p>
      <p className="mt-3 max-w-md text-panel whitespace-pre-line text-foreground">{caption}</p>
    </div>
  );
}

function Label({ children, className }: { children: string; className: string }) {
  return <p className={`kicker mb-3 ${className}`}>{children}</p>;
}

/** How a set of tests ended, as one bar with its three counts. The outcomes are never merged. */
function Outcomes({ counts, height = 28 }: { counts: Record<Outcome, number>; height?: number }) {
  return (
    <div>
      <div className="flex w-full gap-px" style={{ height }} role="img" aria-label={OUTCOMES.map((o) => `${o} ${counts[o]}`).join(", ")}>
        {OUTCOMES.map((o) => (
          <span key={o} style={{ flexGrow: counts[o], flexBasis: 0, background: OUTCOME_COLOR[o] }} />
        ))}
      </div>
      <dl className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-body">
        {OUTCOMES.map((o) => (
          <div key={o} className="flex items-baseline gap-2">
            <span aria-hidden className="size-2 shrink-0 self-center" style={{ background: OUTCOME_COLOR[o] }} />
            <dt className="text-muted-foreground">{o}</dt>
            <dd className="num font-bold text-foreground">{counts[o]}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

/** Horizontal bars, one per row, the count printed at the end of each. */
function Bars({ rows }: { rows: { label: string; value: number; tone: string }[] }) {
  const max = Math.max(...rows.map((r) => r.value));
  return (
    <ul className="space-y-3">
      {rows.map((r) => (
        <li key={r.label} className="grid grid-cols-[minmax(7.5rem,10.5rem)_1fr_2.25rem] items-center gap-x-3 text-body">
          <span className="text-foreground">{r.label}</span>
          <span className="h-6" aria-hidden>
            <span className="block h-full" style={{ width: `${(100 * r.value) / max}%`, background: FILL_TONE[r.tone] }} />
          </span>
          <span className="num text-right font-bold text-foreground">{r.value}</span>
        </li>
      ))}
    </ul>
  );
}

/** One cell per test, in test order, coloured by how the test ended. */
function Waffle() {
  return (
    <div
      className="grid gap-[3px]"
      style={{ gridTemplateColumns: `repeat(${D.waffle_columns}, minmax(0, 1fr))` }}
      role="img"
      aria-label={`${D.tests.length} tests in test order, one cell each: ${OUTCOMES.map((o) => `${o} ${D.outcomes[o]}`).join(", ")}`}
    >
      {D.tests.map((outcome, i) => (
        <span key={i} className="aspect-square" style={{ background: OUTCOME_COLOR[outcome as Outcome] }} />
      ))}
    </div>
  );
}

const steps = (from: number, to: number, step: number) => Array.from({ length: Math.floor((to - from) / step + 1e-9) + 1 }, (_, i) => from + i * step);

/** The share of tests ending in Extinction at each oxygen level tested, one mark per level and fuel. No line is fitted. */
function ShareScatter({ label }: { label: string }) {
  const [x0, x1, dx] = D.o2_axis;
  const [y0, y1, dy] = D.share_axis;
  const W = 640, H = 172, L = 58, R = 14, T = 10, B = 34;      // room for the labels at their phone size
  const px = (v: number) => L + ((v - x0) / (x1 - x0)) * (W - L - R);
  const py = (v: number) => T + (1 - (v - y0) / (y1 - y0)) * (H - T - B);
  return (
    <div>
      <ul className="mb-1 flex gap-5 text-body text-muted-foreground">
        {D.fuels.map((f) => (
          <li key={f.label} className="flex items-center gap-2">
            <span aria-hidden className="size-2 rounded-full" style={{ background: FILL_TONE[f.tone] }} />
            {f.label}
          </li>
        ))}
      </ul>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={label}>
        {steps(y0, y1, dy).map((v) => (
          <g key={v}>
            <line x1={L} x2={W - R} y1={py(v)} y2={py(v)} stroke="var(--line)" />
            <text x={L - 8} y={py(v) + 4} textAnchor="end" fill="var(--muted-foreground)" className="num text-[11px] max-sm:text-[16px]">
              {Math.round(v * 100)}%
            </text>
          </g>
        ))}
        {steps(x0, x1, dx).map((v) => (
          <text key={v} x={px(v)} y={H - 8} textAnchor="middle" fill="var(--muted-foreground)" className="num text-[11px] max-sm:text-[16px]">
            {v}% O2
          </text>
        ))}
        {D.fuels.map((f) =>
          f.share_by_o2.map(([level, share]) => <circle key={`${f.label}-${level}`} cx={px(level)} cy={py(share)} r={4.5} fill={FILL_TONE[f.tone]} />),
        )}
      </svg>
    </div>
  );
}

// ------------------------------------------------------------------------------------------ slides

function SlideTitle() {
  const { words: w, tones, source } = S.title;
  const [team] = w["Team and link"].split(deck.site);
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <div className="mt-6 grid flex-1 grid-cols-1 items-center gap-10 lg:grid-cols-2">
        <div>
          <h2 className="font-heading text-[clamp(2.25rem,5vw,3.75rem)] leading-[1.02] font-bold text-foreground">{w.Title}</h2>
          <p className="mt-5 max-w-xl text-[clamp(1.05rem,1.6vw,1.35rem)] leading-snug text-muted-foreground">{w.Subtitle}</p>
          <p className="mt-8 text-panel text-foreground">{w["One line"]}</p>
          <p className="mt-10 text-body text-muted-foreground">
            {team}
            <Link href="/" className="num text-amber underline-offset-4 hover:underline">
              {deck.site}
            </Link>
          </p>
        </div>
        <div>
          <Hero value={w["Hero number"]} caption={w["Hero number caption"]} className={tone(tones, "Hero number")} size={HUGE} />
          <div className="mt-6">
            <Outcomes counts={D.outcomes} height={36} />
          </div>
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

function SlideProblem() {
  const { words: w, tones, source } = S.problem;
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <h2 className={TITLE}>{w.Title}</h2>
      <p className={`mt-4 ${LINE} max-w-4xl`}>{w.Stakes}</p>
      <div className="mt-8 grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <Hero value={w["Hero number"]} caption={w["Hero number caption"]} className={tone(tones, "Hero number")} />
        <div>
          <Label className={tone(tones, "Chart label")}>{w["Chart label"]}</Label>
          <Bars rows={D.records} />
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

function SlideFlex() {
  const { words: w, tones, source } = S.flex;
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <div className="mt-6 grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div>
          <Hero value={w["Hero number"]} caption={w["Hero number caption"]} className={tone(tones, "Hero number")} size={HUGE} />
          <p className={`mt-8 ${LINE}`}>{w["What it is"]}</p>
          <p className={`mt-4 ${LINE}`}>{w.Method}</p>
        </div>
        <div>
          <Label className={tone(tones, "Chart label")}>{w["Chart label"]}</Label>
          <Waffle />
          <div className="mt-5">
            <Outcomes counts={D.outcomes} height={22} />
          </div>
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

function SlideFuel() {
  const { words: w, tones, source } = S.fuel;
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <h2 className={TITLE}>{w.Title}</h2>
      <div className="mt-6 grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div>
          <Hero value={w["Hero number"]} caption={w["Hero number caption"]} className={tone(tones, "Hero number")} size={MID} />
          <div className="mt-7 grid grid-cols-2 gap-6">
            <Hero value={w["Methanol share"]} caption={w["Methanol share caption"]} className={tone(tones, "Methanol share")} size={SMALL} />
            <Hero value={w["n-Heptane share"]} caption={w["n-Heptane share caption"]} className={tone(tones, "n-Heptane share")} size={SMALL} />
          </div>
          <p className={`mt-7 ${LINE}`}>{w["One line"]}</p>
        </div>
        <div>
          <Label className={tone(tones, "Chart label 1")}>{w["Chart label 1"]}</Label>
          <div className="space-y-3">
            {D.fuels.map((f) => (
              <div key={f.label} className="grid grid-cols-[6.5rem_1fr] items-start gap-x-3">
                <p className={`text-panel font-bold ${TEXT_TONE[f.tone]}`}>{w[`${f.label} label` as "Methanol label" | "n-Heptane label"]}</p>
                <Outcomes counts={f.counts} height={20} />
              </div>
            ))}
          </div>
          <div className="mt-5">
            <Label className={tone(tones, "Chart label 2")}>{w["Chart label 2"]}</Label>
            <ShareScatter label={w["Chart label 2"]} />
          </div>
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

function SlideCool() {
  const { words: w, tones, source } = S.cool;
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <h2 className={TITLE}>{w.Title}</h2>
      <div className="mt-8 grid grid-cols-1 items-start gap-10 lg:grid-cols-2">
        <div>
          <Hero value={w["Hero number"]} caption={w["Hero number caption"]} className={tone(tones, "Hero number")} size={MID} />
          <p className={`mt-10 ${LINE}`}>{w["Why it matters"]}</p>
        </div>
        <div>
          <Label className={tone(tones, "Chart label")}>{w["Chart label"]}</Label>
          <Bars rows={D.cool} />
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

function SlideModel() {
  const { words: w, tones, lead, source, matrix, nearest } = S.model;
  const honest = w["The honest line"];
  const opening = lead["The honest line"];
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <div className="mt-6 grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div>
          <Hero value={w["Hero number"]} caption={w["Hero number caption"]} className={tone(tones, "Hero number")} />
          <p className={`mt-8 ${LINE}`}>{w["What the model is"]}</p>
          <p className={`mt-5 ${LINE}`}>
            <span className={`font-bold ${tone(tones, "The honest line")}`}>{opening}</span>
            {honest.slice(opening.length)}
          </p>
        </div>
        <div>
          <Label className={tone(tones, "Chart label 1")}>{w["Chart label 1"]}</Label>
          <table className="w-full border-separate border-spacing-x-2 border-spacing-y-2 text-body">
            <thead>
              <tr>
                <td />
                {matrix.columns.map((c) => (
                  <th key={c} scope="col" className="pb-1 text-center font-normal text-muted-foreground">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {matrix.rows.map((row) => (
                <tr key={row.label}>
                  <th scope="row" className="pr-2 text-left font-normal text-foreground">
                    {row.label}
                  </th>
                  {row.cells.map((cell, k) => (
                    <td key={k} className={`num w-[28%] border border-line py-4 text-center text-[1.6rem] leading-none font-bold ${cell.red ? "bg-ext text-background" : "bg-surface text-foreground"}`}>
                      {cell.text}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-6">
            <Label className={tone(tones, "Chart label 2")}>{w["Chart label 2"]}</Label>
            <p className={`num text-panel ${tone(tones, "Scenario")}`}>{w.Scenario}</p>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-body">
                <thead>
                  <tr>
                    {nearest.heads.map((h) => (
                      <th key={h} scope="col" className="num pb-2 text-left text-note font-normal text-dim">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {nearest.rows.map((row) => (
                    <tr key={row[0].text} className="border-t border-line">
                      {row.map((cell, k) => (
                        <td key={k} className={`py-2 pr-3 whitespace-nowrap ${cell.tone ? TEXT_TONE[cell.tone] : "num text-foreground"}`}>
                          {cell.text}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

function SlideUnknown() {
  const { words: w, tones, source } = S.unknown;
  const heroes = [["Hero number 1", "Hero number 1 caption"], ["Hero number 2", "Hero number 2 caption"], ["Hero number 3", "Hero number 3 caption"]] as const;
  const panels = [["Panel label 1", "Cannot see"], ["Panel label 2", "Where it stops"]] as const;
  return (
    <>
      <Kicker>{w.Kicker}</Kicker>
      <h2 className={TITLE}>{w.Title}</h2>
      <div className="mt-8 grid grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div>
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-[1fr_1fr_1.3fr]">
            {heroes.map(([name, caption]) => (
              <Hero key={name} value={w[name]} caption={w[caption]} className={tone(tones, name)} size={SMALL} />
            ))}
          </div>
          <p className="mt-10">
            <Link href="/" className={`num text-[clamp(1.25rem,2.6vw,2rem)] font-bold underline-offset-4 hover:underline ${tone(tones, "Live link")}`}>
              {w["Live link"]}
            </Link>
          </p>
          <p className="mt-3 text-panel text-foreground">{w["Last line"]}</p>
        </div>
        <div className="border border-dashed border-dim p-5">
          <span className="num bg-foreground px-2 py-0.5 text-note font-bold tracking-widest text-background">{w["No data tag"]}</span>
          {panels.map(([label, lines]) => (
            <div key={label} className="mt-5">
              <Label className={tone(tones, label)}>{w[label]}</Label>
              <ul className="space-y-1 text-body text-foreground">
                {w[lines].split("\n").map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <Foot>{source}</Foot>
    </>
  );
}

// One entry per slide of the PowerPoint file. A slide added there and not here does not compile.
const RENDER: Record<keyof typeof S, { name: string; render: () => React.ReactNode }> = {
  title: { name: "Title", render: SlideTitle },
  problem: { name: "The problem", render: SlideProblem },
  flex: { name: "The evidence base", render: SlideFlex },
  fuel: { name: "The quantitative core", render: SlideFuel },
  cool: { name: "What extinction hides", render: SlideCool },
  model: { name: "The model and the Scenario Lab", render: SlideModel },
  unknown: { name: "What we don't know, and where to look", render: SlideUnknown },
};
const SLIDES = deck.order.map((key) => RENDER[key as keyof typeof S]);

// ------------------------------------------------------------------------------------------ deck

interface Travel {
  d: number;
  instant: boolean;
}

export function Deck() {
  // [slide, direction of travel, show at once]. A slide opened from a link appears at once;
  // only a change made by the reader is animated, so nothing depends on an animation finishing.
  const [[index, direction, instant], setPage] = useState<[number, number, boolean]>([0, 1, false]);
  const touch = useRef<number | null>(null);
  const [printing, setPrinting] = useState(false);

  useEffect(() => {
    const before = () => flushSync(() => setPrinting(true)); // the copies must be in the page before it is laid out for print
    const after = () => setPrinting(false);
    window.addEventListener("beforeprint", before);
    window.addEventListener("afterprint", after);
    return () => {
      window.removeEventListener("beforeprint", before);
      window.removeEventListener("afterprint", after);
    };
  }, []);
  const go = useCallback((to: number) => setPage(([cur]) => {
    const next = Math.min(SLIDES.length - 1, Math.max(0, to));
    return [next, next >= cur ? 1 : -1, false];
  }), []);

  // the slide number lives in the address bar's hash: no navigation, no reload
  useEffect(() => {
    const n = Number(window.location.hash.replace("#", ""));
    // reading the address bar is only possible after mounting
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (n >= 1 && n <= SLIDES.length) setPage([n - 1, 1, true]);
  }, []);
  useEffect(() => {
    const hash = `#${index + 1}`;
    if (index === 0 && !window.location.hash) return; // the first slide needs no hash: leave the address as it was opened
    if (window.location.hash !== hash) window.history.replaceState(window.history.state, "", `${window.location.pathname}${window.location.search}${hash}`);
  }, [index]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      const target = e.target as HTMLElement | null;
      if (target && (target.closest("a, button, input, select, textarea") || target.isContentEditable)) {
        if (e.key === " " || e.key === "Enter") return; // let a focused control act
      }
      if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") { e.preventDefault(); setPage(([cur]) => [Math.min(SLIDES.length - 1, cur + 1), 1, false]); }
      else if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); setPage(([cur]) => [Math.max(0, cur - 1), -1, false]); }
      else if (e.key === "Home") { e.preventDefault(); setPage([0, -1, false]); }
      else if (e.key === "End") { e.preventDefault(); setPage([SLIDES.length - 1, 1, false]); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const Current = SLIDES[index].render;
  const travel: Travel = { d: direction, instant };
  const counter = `${index + 1} / ${SLIDES.length}`;

  return (
    <>
      <div
        className="flex min-h-dvh flex-col bg-background print:hidden"
        onTouchStart={(e) => { touch.current = e.touches[0].clientX; }}
        onTouchEnd={(e) => {
          if (touch.current === null) return;
          const dx = e.changedTouches[0].clientX - touch.current;
          touch.current = null;
          if (Math.abs(dx) > 60) go(index + (dx < 0 ? 1 : -1)); // swipe left for the next slide
        }}
      >
        <header className="glass-rail flex h-12 shrink-0 items-center justify-between border-b border-line px-4 sm:px-8">
          <Link href="/" className="font-heading text-panel font-bold tracking-[0.18em] text-foreground">
            FLAMEFALL
          </Link>
          <p className="num text-note text-muted-foreground" aria-live="polite">
            <span className="sr-only">Slide </span>
            {counter}
          </p>
        </header>

        <main className="relative flex-1 overflow-x-hidden">
          <AnimatePresence mode="wait" custom={travel} initial={false}>
            <motion.section
              key={index}
              custom={travel}
              aria-label={`Slide ${index + 1} of ${SLIDES.length}: ${SLIDES[index].name}`}
              variants={{
                enter: (t: Travel) => (t.instant ? { opacity: 1, x: 0 } : { opacity: 0, x: 28 * t.d }),
                centre: { opacity: 1, x: 0 },
                exit: (t: Travel) => (t.instant ? { opacity: 0, transition: { duration: 0 } } : { opacity: 0, x: -28 * t.d }),
              }}
              initial="enter"
              animate="centre"
              exit="exit"
              transition={{ duration: 0.26 }}
              className="mx-auto flex min-h-[calc(100dvh-8.25rem)] w-full max-w-[1200px] flex-col px-4 py-6 sm:px-8"
            >
              <Current />
            </motion.section>
          </AnimatePresence>
        </main>

        <footer className="glass-rail flex h-14 shrink-0 items-center justify-between gap-3 border-t border-line px-4 sm:px-8">
          <Button variant="outline" size="sm" className="rounded-sm" onClick={() => go(index - 1)} disabled={index === 0}>
            <ChevronLeft aria-hidden /> <span className="hidden sm:inline">Previous</span>
          </Button>
          <ol className="flex items-center gap-1.5" aria-label="Slides">
            {SLIDES.map((s, i) => (
              <li key={s.name}>
                <button
                  type="button"
                  aria-label={`Slide ${i + 1}: ${s.name}`}
                  aria-current={i === index ? "step" : undefined}
                  onClick={() => go(i)}
                  className="flex h-8 w-5 items-center justify-center outline-none focus-visible:ring-1 focus-visible:ring-amber sm:w-7"
                >
                  <span className={`block h-0.5 w-full transition-all ${i === index ? "bg-amber" : "bg-input"}`} />
                </button>
              </li>
            ))}
          </ol>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={() => go(index + 1)} disabled={index === SLIDES.length - 1}>
            <span className="hidden sm:inline">Next</span> <ChevronRight aria-hidden />
          </Button>
        </footer>
        {/* Outside the slides: what the console's sidebar says on every other page. */}
        <p className="h-7 shrink-0 px-4 text-center text-note leading-7 text-dim sm:px-8">
          Not affiliated with or endorsed by NASA
          {" · "}
          <a href={`${REPO_URL}/blob/main/docs/SI_DISCLOSURE.md`} target="_blank" rel="noopener" className="underline decoration-line hover:text-foreground">
            Use of SI tools
          </a>
        </p>
      </div>

      {/* Printing gives every slide, one per page. The copies exist only while printing. */}
      {printing && (
      <div className="hidden print:block">
        {SLIDES.map((s, i) => (
          <section key={s.name} className="flex min-h-screen break-after-page flex-col px-8 py-10">
            <p className="num mb-4 text-note text-muted-foreground">
              {i + 1} / {SLIDES.length}
            </p>
            <s.render />
          </section>
        ))}
      </div>
      )}
    </>
  );
}
