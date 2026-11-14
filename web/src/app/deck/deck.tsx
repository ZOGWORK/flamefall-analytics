"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, ChevronLeft, ChevronRight, LayoutDashboard } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";

import { OutcomeStrip } from "@/components/charts/outcome-strip";
import { CountBars } from "@/components/charts/unknown-charts";
import { Kicker, NoData, Num, Prose } from "@/components/console/primitives";
import { REPO_URL } from "@/components/shell/nav";
import { Button } from "@/components/ui/button";
import coolJson from "@/data/model_droplet_cool_flame.json";
import extinctionJson from "@/data/model_droplet_extinction.json";
import solidJson from "@/data/model_solid_sustained.json";
import { catalogue, ev, flex, panels, solid } from "@/lib/data";
import { pct } from "@/lib/format";
import { hazard, R, scenario, TERM_KEYS } from "@/lib/ranking";
import type { ModelCard } from "@/lib/types";

const EXT = extinctionJson as unknown as ModelCard;
const COOL = coolJson as unknown as ModelCard;
const SOLID = solidJson as unknown as ModelCard;
const S = flex.summary;
const N = catalogue.counts;
const REPORT = flex.meta.report;
const f2 = (v: number | null) => (v === null ? "n/a" : v.toFixed(2));

function Foot({ children }: { children: string }) {
  return (
    <p className="mt-auto pt-5 text-note text-muted-foreground">
      <span className="text-dim">Source: </span>
      <Prose text={children} />
    </p>
  );
}

function Stat({ value, label, source, tone = "text-amber" }: { value: React.ReactNode; label: string; source: string; tone?: string }) {
  return (
    <div className="border-t border-line pt-3">
      <p className={`num text-[clamp(1.75rem,4vw,2.75rem)] leading-none font-bold ${tone}`}>{value}</p>
      <p className="mt-2 text-body text-foreground">
        <Prose text={label} />
      </p>
      <p className="mt-1 text-note text-muted-foreground">
        <Prose text={source} />
      </p>
    </div>
  );
}

function Title({ children }: { children: React.ReactNode }) {
  return <h2 className="mt-3 max-w-4xl text-[clamp(1.5rem,3.6vw,2.5rem)] leading-[1.1] font-semibold text-foreground">{children}</h2>;
}

function Bar({ label, value, max, text, color }: { label: string; value: number; max: number; text: string; color: string }) {
  return (
    <div className="grid grid-cols-[1fr_auto] items-baseline gap-x-3">
      <span className="text-body text-muted-foreground">{label}</span>
      <span className="num text-body text-foreground">{text}</span>
      <span className="col-span-2 mt-1 h-2 bg-secondary" aria-hidden>
        <motion.span className="block h-full origin-left" style={{ width: `${(100 * value) / max}%`, background: color }} initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 0.6, delay: 0.15 }} />
      </span>
    </div>
  );
}

// ------------------------------------------------------------------------------------------ slides

function SlideTitle() {
  return (
    <>
      <Kicker>Space Apps 2026 · Flame in Freefall · Team Flamefall Analytics</Kicker>
      <h2 className="mt-4 max-w-5xl text-[clamp(2rem,5.4vw,4rem)] leading-[1.02] font-bold text-foreground">
        Fire behaves differently in space. <span className="text-amber">We show what was actually measured.</span>
      </h2>
      <p className="mt-5 max-w-2xl text-panel text-muted-foreground">
        A console that summarises, ranks and interprets microgravity combustion experiments for people designing crewed vehicles and
        habitats. Every number carries its source. Where nobody ran the test, it says “no data”.
      </p>
      <div className="mt-8 grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-3">
        <Stat value={S.n} label="droplet burns in the core dataset" source={`${REPORT}, Table IX`} />
        <Stat value={solid.n_decided} label="solid-fuel test points with a stated outcome" source="NASA/TM-20210011385; PSI-99; ICES-2024-365; ICES-2025-156; NTRS 20240007628" tone="text-foreground" />
        <Stat value={N.evidence} label="sourced statements, each with a quote and a read level" source="evidence table in the repository" tone="text-foreground" />
      </div>
      <div className="mt-8 flex flex-wrap gap-3">
        <Button className="rounded-sm" size="lg" render={<Link href="/" />}>
          <LayoutDashboard aria-hidden /> Open the live console
        </Button>
        <Button variant="outline" className="rounded-sm" size="lg" render={<a href={REPO_URL} target="_blank" rel="noopener" />}>
          Code and data <ArrowUpRight aria-hidden />
        </Button>
      </div>
    </>
  );
}

function SlideProblem() {
  const brief = ev("brief-atmospheres");
  const rows = [
    { label: "Sea-level air (reference)", o2: 21, psi: 14.7, note: "21% O2 at 14.7 psi" },
    { label: "Moon base or rover cabin (expected)", o2: 30, psi: 10.2, note: "30% O2 or more at 10.2 psi or less" },
    { label: "Spacesuit", o2: 100, psi: 4.3, note: "100% O2 at 4.3 psi" },
  ];
  return (
    <>
      <Kicker>The problem</Kicker>
      <Title>
        Future cabins move towards <span className="text-amber">more oxygen and less pressure</span>. The evidence is scattered.
      </Title>
      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div className="space-y-5">
          {rows.map((r) => (
            <div key={r.label}>
              <p className="text-body text-foreground">{r.label}</p>
              <div className="mt-1.5 space-y-1.5">
                <Bar label="oxygen fraction" value={r.o2} max={100} text={`${r.o2}%`} color="var(--amber)" />
                <Bar label="total pressure" value={r.psi} max={14.7} text={`${r.psi} psi`} color="var(--data)" />
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-4">
            <Stat value={N.search_hits} label="records returned for “combustion”" source="PSI search" tone="text-foreground" />
            <Stat value={N.combustion_science} label="are combustion science" source="PSI research area" tone="text-foreground" />
            <Stat value={N.tables} label="per-test tables, in different shapes and units" source="copied to the repository" tone="text-foreground" />
          </div>
          <p className="border-l-2 border-amber pl-4 text-panel text-foreground">
            Droplets, gas flames, solids and smoke obey different physics. <span className="text-amber">We never pool them.</span>
          </p>
          <p className="text-body text-muted-foreground">
            Three rules on every page: a source under every number · “no data” is an answer · estimates, never verdicts.
          </p>
        </div>
      </div>
      <Foot>{`${brief.source_ref}: “${brief.statement}” Sea-level air is shown for reference. PSI Data Repository search “combustion”, retrieved ${N.retrieved.slice(0, 10)}.`}</Foot>
    </>
  );
}

function SlideFlex() {
  const meth = S.by_fuel.Methanol;
  const hept = S.by_fuel.Heptane;
  return (
    <>
      <Kicker>The quantitative core · FLEX droplet experiment</Kicker>
      <Title>
        <Num className="text-amber">{S.n}</Num> droplet burns. Fuel chemistry matters as much as atmosphere.
      </Title>
      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div>
          <p className="kicker mb-2 text-dim">How the {S.n} tests ended · three outcomes, never merged</p>
          <OutcomeStrip counts={S.outcomes} height={32} />
          <div className="mt-6 space-y-3">
            <Bar label="Methanol: tests ending in Extinction" value={meth.extinction_share} max={1} text={`${meth.Extinction} of ${meth.n} · ${pct(meth.extinction_share)}`} color="var(--data)" />
            <Bar label="n-Heptane: tests ending in Extinction" value={hept.extinction_share} max={1} text={`${hept.Extinction} of ${hept.n} · ${pct(hept.extinction_share)}`} color="var(--amber)" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-5">
          <Stat value="3,864" label="cells re-read from the PDF with a second parser: all match" source="scripts/verify_flex_table_ix.py" tone="text-done" />
          <Stat value="274" label="rows in the repository's own table: all match but one documented cell" source="PSI-69 table; tests/test_psi.py" tone="text-done" />
          <Stat value={S.ranges.extinction_diameter_mm[3]} label="tests print no extinction diameter. None is filled in" source={`${REPORT}, Table IX`} tone="text-foreground" />
          <Stat value={`${pct(S.ranges.o2[0], 0)}–${pct(S.ranges.o2[1], 0)}`} label={`oxygen range tested; CO2 up to ${pct(S.ranges.co2[1], 0)}, helium up to ${pct(S.ranges.he[1], 0)}`} source={`${REPORT}, Table IX`} tone="text-foreground" />
        </div>
      </div>
      <Foot>{`${REPORT} (Dietrich et al., 2015), Table IX. Totals recomputed from the data by the test suite. Disruption may reflect needle-coating contamination (report §5.2) and is not an extinction.`}</Foot>
    </>
  );
}

function SlideUnseen() {
  const c = S.cool_flame;
  const kapton = panels.smoke.flights[0].rows[0];
  const alarm = ev("saffire-alarm-981");
  const misses = ev("same-detector-misses");
  return (
    <>
      <Kicker>What you can&apos;t see</Kicker>
      <Title>
        “No visible flame” is <span className="text-ext">not</span> “fire out”.
      </Title>
      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div>
          <p className="kicker mb-3 text-dim">
            {S.heptane_extinctions} n-heptane tests logged as “Extinction”
          </p>
          <CountBars
            total={S.heptane_extinctions}
            rows={[
              { label: "Cool-flame evidence", value: c.indicated, color: "var(--amber)" },
              { label: "No evidence", value: c.not_indicated, color: "var(--data)" },
              { label: "Unclear", value: c.unclear, color: "var(--dim)" },
              { label: "Caption silent", value: c[""], color: "var(--input)" },
            ]}
          />
          <p className="mt-4 text-body text-muted-foreground">
            In <Num className="text-foreground">{c.indicated}</Num> of <Num className="text-foreground">{S.heptane_extinctions}</Num> the droplet kept
            vaporising after the flame disappeared: a cool flame, with nothing to see.
          </p>
        </div>
        <div className="grid grid-cols-1 gap-y-5 sm:grid-cols-3 sm:gap-x-5 lg:grid-cols-1 xl:grid-cols-3">
          <Stat value="½ · ⅔" label="of Kapton and of Teflon smoke tests in which the station-type detector did not alarm" source={misses.source_ref} tone="text-ext" />
          <Stat value={<>{kapton.fresh}<span className="ml-1 text-note text-muted-foreground">nm</span></>} label={`geometric mean size of fresh Kapton smoke, far below ${panels.smoke.threshold_nm} nm`} source={ev("same1-table1").source_ref} tone="text-data" />
          <Stat value={<>{alarm.value}<span className="ml-1 text-note text-muted-foreground">s</span></>} label="for a far-field detector to reach its alarm threshold in a vehicle-scale burn" source={alarm.source_ref} tone="text-foreground" />
        </div>
      </div>
      <Foot>{`${REPORT}, Appendix B: one figure caption per test, read for the authors' statement on vaporisation and vapour cloud after the visible flame vanished. Each label is stored with its sentence.`}</Foot>
    </>
  );
}

function SlideMethod() {
  const base = scenario({ name: "base", material: "PMMA", o2_pct: 21, pressure_kpa: 101, flow_cm_s: 20, gravity_g: 0 });
  const lunar = { ...base, gravity_g: 0.16 };
  const limit = { ...base, o2_pct: 13.6 };
  const em = EXT.metrics;
  return (
    <>
      <Kicker>How the intelligence layer works</Kicker>
      <Title>Three auditable steps. None of them can invent a number.</Title>
      <div className="mt-6 grid grid-cols-1 gap-px border border-line bg-line lg:grid-cols-3">
        <div className="flex flex-col bg-surface p-4">
          <p className="kicker text-data">1 · Retrieve</p>
          <p className="mt-2 text-panel font-semibold text-foreground">Search returns the measured statements themselves</p>
          <p className="mt-2 text-body text-muted-foreground">
            A question is scored against <Num>{N.evidence}</Num> sourced statements and the catalogue. The answer is extraction only: no
            text is generated. An oxygen limit in the question becomes a filter on recorded ambient ranges, and burner-feed values are
            never matched.
          </p>
        </div>
        <div className="flex flex-col bg-surface p-4">
          <p className="kicker text-amber">2 · Rank</p>
          <p className="mt-2 text-panel font-semibold text-foreground">A stated formula with visible weights</p>
          <p className="num mt-2 text-note text-foreground">Hazard = {TERM_KEYS.map((k) => `${R.weights[k].toFixed(2)} ${k}`).join(" + ")}</p>
          <dl className="mt-3 space-y-1 text-body">
            {[["Acrylic rod, station air, microgravity", hazard(base)], ["Same, lunar gravity", hazard(lunar)], ["Same, at the oxygen limit", hazard(limit)]].map(([label, v]) => (
              <div key={label as string} className="flex justify-between gap-3 border-b border-line py-1">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="num text-foreground">{(v as number).toFixed(3)}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-2 text-note text-muted-foreground">Every weight moved by ±0.10 to see whether the order survives. It orders scenarios; it is not a risk rating.</p>
        </div>
        <div className="flex flex-col bg-surface p-4">
          <p className="kicker text-ext">3 · Estimate</p>
          <p className="mt-2 text-panel font-semibold text-foreground">Small models, scored on groups they never saw</p>
          <dl className="mt-2 space-y-1 text-body">
            <div className="flex justify-between gap-3 border-b border-line py-1">
              <dt className="text-muted-foreground">Droplet extinction, grouped CV</dt>
              <dd className="num text-foreground">{f2(em.roc_auc)}</dd>
            </div>
            <div className="flex justify-between gap-3 border-b border-line py-1">
              <dt className="text-muted-foreground">Same, leave-one-fuel-out (headline)</dt>
              <dd className="num text-amber">{f2(EXT.headline_auc)}</dd>
            </div>
            <div className="flex justify-between gap-3 border-b border-line py-1">
              <dt className="text-muted-foreground">Cool-flame evidence (exploratory)</dt>
              <dd className="num text-foreground">{f2(COOL.metrics.roc_auc)}</dd>
            </div>
            <div className="flex justify-between gap-3 border-b border-line py-1">
              <dt className="text-muted-foreground">Solid materials: fails, shown failing</dt>
              <dd className="num text-ext">{f2(SOLID.metrics.roc_auc)}</dd>
            </div>
          </dl>
          <p className="mt-2 text-note text-muted-foreground">
            The headline is the worse of two validations. Every estimate carries its distance to the training data; outside it, the output
            is labelled DEMO.
          </p>
        </div>
      </div>
      <Foot>{`AUC values from data/models in the repository (seed 42, folds saved). Droplet extinction 95% interval ${f2(em.roc_auc_ci[0])} to ${f2(em.roc_auc_ci[1])}; cool-flame ${f2(COOL.metrics.roc_auc_ci[0])} to ${f2(COOL.metrics.roc_auc_ci[1])} on ${COOL.n_rows} tests; solids ${f2(SOLID.metrics.roc_auc_ci[0])} to ${f2(SOLID.metrics.roc_auc_ci[1])}. Formula and lookup values: flamefall/ranking.py.`}</Foot>
    </>
  );
}

function SlideLimits() {
  const env = solid.envelope_all;
  return (
    <>
      <Kicker>Where the data stops</Kicker>
      <Title>The most useful answer is sometimes “nobody has run this test”.</Title>
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <NoData title="Partial gravity" note="Source: official challenge brief; PSI search.">
          {`0 combustion tests in lunar or Martian gravity are in the repository. The nearest real evidence is one suborbital flight: fabric spread at ${panels.luci.rows[0].lunar} mm/s in simulated lunar gravity against ${panels.luci.rows[0].earth} mm/s in normal gravity.`}
        </NoData>
        <NoData title="Solids above 34% oxygen" note={`Source: ${solid.n_decided} solid-fuel test points with a stated outcome; see the console's gaps page.`}>
          {`No solid-material test point exists above 34% O2 at any pressure. The highest with a stated outcome is ${env.o2?.[1].toFixed(1)}%, the highest with a sustained flame ${env.sustained_o2_max?.toFixed(1)}%.`}
        </NoData>
        <NoData title="CO2 and helium together" note={`Source: ${REPORT}, Table IX.`}>
          {`${S.co2_and_he} of ${S.n} droplet tests contain both diluents. CO2 was present in ${S.co2_tests} tests and helium in ${S.he_tests}; helium's own effect is unclear.`}
        </NoData>
      </div>
      <blockquote className="mt-6 border-l border-dim pl-4 text-body text-foreground italic">
        <Prose text={panels.partial_gravity_wording} />
      </blockquote>
      <p className="mt-3 text-body text-muted-foreground">
        <Prose text={ev("fm2-plan").statement} />
      </p>
      <Foot>{`${panels.luci.source_ref}. ${ev("fm2-plan").source_ref}.`}</Foot>
    </>
  );
}

function SlideClose() {
  return (
    <>
      <Kicker>What a designer leaves with</Kicker>
      <Title>
        Measurements with their sources, the nearest real test to a scenario, and an honest map of the gaps. <span className="text-amber">Estimates, never verdicts.</span>
      </Title>
      <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div>
          <p className="kicker text-dim">Use of SI tools</p>
          <ul className="mt-2 list-disc space-y-1.5 pl-5 text-body text-muted-foreground marker:text-dim">
            <li>Research notes were compiled by an SI research assistant, then checked against primary sources; every correction is logged.</li>
            <li>Code, data pipeline, console and this deck were written with an SI coding agent directed by the team, and reviewed by an SI code-review bot.</li>
            <li>Inside the console there is no generative model: retrieval, a stated formula, and small validated classifiers.</li>
            <li>No SI-generated images, video or audio. Every chart is drawn from the data by code.</li>
          </ul>
          <p className="mt-2 text-note text-muted-foreground">Full disclosure: docs/SI_DISCLOSURE.md in the repository.</p>
        </div>
        <div>
          <p className="kicker text-dim">Open and reproducible</p>
          <ul className="mt-2 list-disc space-y-1.5 pl-5 text-body text-muted-foreground marker:text-dim">
            <li>MIT licence. Public data from NASA&apos;s Physical Sciences Informatics repository and NASA technical reports.</li>
            <li>One command rebuilds the core table from the PDF and compares every cell.</li>
            <li>Not affiliated with or endorsed by NASA. No agency logos or marks are used.</li>
          </ul>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button className="rounded-sm" size="lg" render={<Link href="/" />}>
              <LayoutDashboard aria-hidden /> Open the live console
            </Button>
            <Button variant="outline" className="rounded-sm" size="lg" render={<a href={REPO_URL} target="_blank" rel="noopener" />}>
              Code and data <ArrowUpRight aria-hidden />
            </Button>
          </div>
        </div>
      </div>
      <Foot>{`${REPORT}; NASA/TM-20210011385; PSI Data Repository (CC0-1.0); papers cited per statement in the console.`}</Foot>
    </>
  );
}

const SLIDES: { name: string; render: () => React.ReactNode }[] = [
  { name: "Title", render: SlideTitle },
  { name: "The problem", render: SlideProblem },
  { name: "FLEX: the quantitative core", render: SlideFlex },
  { name: "What you can't see", render: SlideUnseen },
  { name: "How the intelligence layer works", render: SlideMethod },
  { name: "Where the data stops", render: SlideLimits },
  { name: "What a designer leaves with", render: SlideClose },
];

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
  const counter = `${String(index + 1).padStart(2, "0")} / ${String(SLIDES.length).padStart(2, "0")}`;

  return (
    <>
      <div
        className="flex min-h-dvh flex-col print:hidden"
        onTouchStart={(e) => { touch.current = e.touches[0].clientX; }}
        onTouchEnd={(e) => {
          if (touch.current === null) return;
          const dx = e.changedTouches[0].clientX - touch.current;
          touch.current = null;
          if (Math.abs(dx) > 60) go(index + (dx < 0 ? 1 : -1)); // swipe left for the next slide
        }}
      >
        <header className="flex h-12 shrink-0 items-center justify-between border-b border-line px-4 sm:px-8">
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
              className="mx-auto flex min-h-[calc(100dvh-6.5rem)] w-full max-w-[1200px] flex-col px-4 py-8 sm:px-8 sm:py-10"
            >
              <Current />
            </motion.section>
          </AnimatePresence>
        </main>

        <footer className="flex h-14 shrink-0 items-center justify-between gap-3 border-t border-line px-4 sm:px-8">
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
                  <span className={`block h-0.5 w-full transition-colors ${i === index ? "bg-amber" : "bg-input"}`} />
                </button>
              </li>
            ))}
          </ol>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={() => go(index + 1)} disabled={index === SLIDES.length - 1}>
            <span className="hidden sm:inline">Next</span> <ChevronRight aria-hidden />
          </Button>
        </footer>
      </div>

      {/* Printing gives every slide, one per page. The copies exist only while printing. */}
      {printing && (
      <div className="hidden print:block">
        {SLIDES.map((s, i) => (
          <section key={s.name} className="flex min-h-screen break-after-page flex-col px-8 py-10">
            <p className="num mb-4 text-note text-muted-foreground">
              {String(i + 1).padStart(2, "0")} / {String(SLIDES.length).padStart(2, "0")}
            </p>
            <s.render />
          </section>
        ))}
      </div>
      )}
    </>
  );
}
