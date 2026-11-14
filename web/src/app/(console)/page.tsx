import { ArrowRight } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { OutcomeStrip } from "@/components/charts/outcome-strip";
import { Decode } from "@/components/console/decode";
import { TestMatrix } from "@/components/console/fx";
import { Kicker, NoDataTag, Prose, Section, Source, Tile, TileRow } from "@/components/console/primitives";
import { PAGES } from "@/components/shell/nav";
import { catalogue, ev, flex, solid, SRC_RECOMPUTED } from "@/lib/data";
import { pct } from "@/lib/format";
import { OverviewCharts } from "./overview-charts";

export const metadata: Metadata = { title: "Overview" };

export default function Overview() {
  const s = flex.summary;
  const meth = s.by_fuel.Methanol;
  const hept = s.by_fuel.Heptane;
  const n = catalogue.counts;
  const cool = s.cool_flame;
  const env = solid.envelope_all;
  const partialG = catalogue.investigations.filter((r) => r.in_psi_search && typeof r.gravity_g === "number" && r.gravity_g > 0.05 && r.gravity_g < 0.5).length;

  const channels: { value: string; label: string; source: string; tone: string }[] = [
    { value: pct(s.extinction_share), label: "ended with the visible flame going out", source: `${SRC_RECOMPUTED} · ${s.outcomes.Extinction} of ${s.n}`, tone: "text-ext" },
    { value: `${pct(meth.extinction_share)} / ${pct(hept.extinction_share)}`, label: "extinction share, methanol / n-heptane", source: `${SRC_RECOMPUTED} · ${meth.Extinction} of ${meth.n} / ${hept.Extinction} of ${hept.n}`, tone: "text-data" },
    { value: `${cool.indicated} of ${s.heptane_extinctions}`, label: "n-heptane “extinctions” that kept burning as a cool flame", source: `${flex.meta.report}, Appendix B captions`, tone: "text-amber" },
    { value: `${n.search_hits}`, label: `repository records for “combustion”, ${n.combustion_science} combustion science`, source: `PSI search, retrieved ${n.retrieved.slice(0, 10)} · ${n.tables} tables copied`, tone: "text-foreground" },
    { value: `${solid.n_decided}`, label: "solid-fuel test points with a stated outcome", source: "NASA/TM-20210011385; PSI-99; ICES-2024-365; ICES-2025-156; NTRS 20240007628", tone: "text-foreground" },
    { value: `${n.evidence}`, label: `sourced statements, ${n.evidence_verified} verified in full text`, source: `evidence table · ${n.evidence_index} abstract-only, ${n.evidence_unverified} not verified and marked`, tone: "text-foreground" },
  ];

  return (
    <>
      <header>
        <Kicker>Space Apps 2026 · Flame in Freefall</Kicker>
        <h1 className="mt-2 max-w-4xl text-heading font-semibold text-foreground">
          Fire behaves differently in space. <span className="text-amber">This console shows what was actually measured.</span>
        </h1>
        <p className="mt-1.5 max-w-3xl text-body text-muted-foreground">Every number carries its source. Where nobody ran the test, it says “no data”.</p>
      </header>

      <section className="beam grid grid-cols-1 border border-line bg-surface xl:grid-cols-12">
        <div className="scan p-4 sm:p-6 xl:col-span-7 xl:border-r xl:border-line">
          <Kicker className="text-dim">The quantitative core — FLEX droplet experiment</Kicker>
          <p className="glow num mt-3 text-[clamp(5rem,15vw,10rem)] leading-[0.85] font-bold tracking-tight text-amber">
            <Decode text={String(s.n)} />
          </p>
          <p className="mt-3 text-body text-foreground">droplet burns on the space station, one row each in Table IX.</p>
          <div className="mt-6">
            <p className="kicker mb-2 text-dim">How the {s.n} tests ended</p>
            <OutcomeStrip counts={s.outcomes} height={36} />
          </div>
          <div className="mt-5">
            <p className="kicker mb-2 text-dim">Every test, in test order · one cell each</p>
            <TestMatrix />
          </div>
          <Source href={flex.meta.record_url}>{`${flex.meta.report}, Table IX · tests ${s.first_test} to ${s.last_test}. Totals recomputed from the data.`}</Source>
        </div>
        <dl className="grid grid-cols-1 sm:grid-cols-2 xl:col-span-5 xl:grid-cols-1">
          {channels.map((c) => (
            <div key={c.label} className="border-t border-line px-4 py-3 sm:px-6 xl:first:border-t-0">
              <dd className={`num text-heading leading-tight font-medium ${c.tone}`}>
                <Decode text={c.value} />
              </dd>
              <dt className="text-body text-foreground">{c.label}</dt>
              <dd className="mt-0.5 text-note text-muted-foreground">
                <Prose text={c.source} />
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <Section title="What the droplet tests show" explainer="Oxygen, fuel, and what the word “extinction” leaves out.">
        <OverviewCharts />
      </Section>

      <Section title="The dangerous combination" explainer="Four conditions future crewed vehicles push towards at the same time.">
        <TileRow>
          <Tile value="30%+" unit="O2" tone="amber" label="expected in Moon-base and rover cabins, at 10.2 psi or less" source={ev("brief-atmospheres").source_ref} />
          <Tile value={`${cool.indicated} of ${s.heptane_extinctions}`} tone="ext" label="“no visible flame” was not “fire out”: a cool flame kept burning" source={`${flex.meta.report}, Appendix B captions`} />
          <Tile value={`${env.o2?.[1].toFixed(1)}%`} tone="data" label="highest oxygen level of any solid-fuel test point; nothing above 34%" source={`${solid.n_decided} solid-fuel test points with a stated outcome`} />
          <Tile value={partialG} tone="dim" tag={<NoDataTag />} label="combustion tests in lunar or Martian gravity in the repository" source={ev("brief-no-partial-g").source_ref} />
        </TileRow>
      </Section>

      <Section title="Where to look" explainer="Each page answers one question.">
        <ul className="overflow-hidden rounded-xl border border-line bg-surface">
          {PAGES.filter((p) => p.href !== "/").map((p) => (
            <li key={p.href} className="border-b border-line last:border-b-0">
              <Link
                href={p.href}
                className="group grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-0.5 px-4 py-2.5 outline-none hover:bg-accent focus-visible:bg-accent sm:grid-cols-[9rem_14rem_1fr_auto]"
              >
                <span className="num hidden text-note text-dim sm:block">{p.href}</span>
                <span className="text-panel font-semibold text-foreground">{p.label}</span>
                <span className="col-span-2 text-body text-muted-foreground sm:col-span-1">{p.question}</span>
                <ArrowRight aria-hidden className="col-start-2 row-start-1 size-4 text-dim transition-transform group-hover:translate-x-0.5 group-hover:text-amber sm:col-start-4" />
              </Link>
            </li>
          ))}
        </ul>
        <Source href={flex.meta.record_url}>
          {`FLEX data: ${flex.meta.report}, PSI record ${flex.meta.psi_id}. A builder-discovered primary source, not a link supplied on the challenge page.`}
        </Source>
      </Section>
    </>
  );
}
