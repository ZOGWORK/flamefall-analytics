import { ArrowRight, BadgeCheck, Droplets, EyeOff, Flame, Layers, Library, Moon, Thermometer } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { OutcomeStrip } from "@/components/charts/outcome-strip";
import { Decode } from "@/components/console/decode";
import { TestMatrix } from "@/components/console/fx";
import { Kicker, NoDataTag, Section, Source, Tile, TileRow } from "@/components/console/primitives";
import { Block, CellMatrix, IconChip, Meter } from "@/components/console/viz";
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
  const solidCount = (outcome: string) => solid.points.filter((p) => p.outcome === outcome).length;

  return (
    <>
      <header>
        <Kicker>Space Apps 2026 · Flame in Freefall</Kicker>
        <h1 className="mt-2 max-w-4xl text-heading font-semibold text-foreground">
          Fire behaves differently in space. <span className="text-amber">This console shows what was actually measured.</span>
        </h1>
        <p className="mt-1.5 max-w-3xl text-body text-muted-foreground">Every number carries its source. Where nobody ran the test, it says “no data”.</p>
      </header>

      <section className="beam grid grid-cols-1 gap-px border border-line bg-line xl:grid-cols-12">
        <div className="scan bg-surface p-4 sm:p-6 xl:col-span-6">
          <div className="flex items-start justify-between gap-3">
            <Kicker className="text-dim">The quantitative core — FLEX droplet experiment</Kicker>
            <IconChip icon={Droplets} tone="amber" />
          </div>
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

        <div className="grid grid-cols-1 gap-px bg-line sm:grid-cols-2 xl:col-span-6">
          <Block icon={Flame} tone="ext" value={<Decode text={pct(s.extinction_share)} />} label="ended with the visible flame going out" source={`${SRC_RECOMPUTED} · ${s.outcomes.Extinction} of ${s.n}`}>
            <Meter value={s.extinction_share} tone="ext" label={`${s.outcomes.Extinction} of ${s.n} tests ended in Extinction`} />
          </Block>
          <Block icon={Droplets} tone="data" value={<Decode text={`${pct(meth.extinction_share)} / ${pct(hept.extinction_share)}`} />} label="extinction share, methanol / n-heptane" source={`${SRC_RECOMPUTED} · ${meth.Extinction} of ${meth.n} / ${hept.Extinction} of ${hept.n}`}>
            <div className="space-y-1.5">
              <Meter value={meth.extinction_share} tone="data" label={`Methanol: ${meth.Extinction} of ${meth.n}`} />
              <Meter value={hept.extinction_share} tone="amber" label={`n-Heptane: ${hept.Extinction} of ${hept.n}`} />
            </div>
          </Block>
          <Block icon={EyeOff} tone="amber" value={<Decode text={`${cool.indicated} of ${s.heptane_extinctions}`} />} label="n-heptane “extinctions” that kept burning as a cool flame" source={`${flex.meta.report}, Appendix B captions`}>
            <CellMatrix
              label={`${cool.indicated} with cool-flame evidence, ${cool.not_indicated} without, ${cool.unclear} unclear, ${cool[""]} caption silent`}
              groups={[
                { n: cool.indicated, color: "var(--amber)", name: "cool-flame evidence" },
                { n: cool.not_indicated, color: "var(--data)", name: "no evidence" },
                { n: cool.unclear, color: "var(--dim)", name: "unclear" },
                { n: cool[""], color: "rgba(255,255,255,0.14)", name: "caption silent" },
              ]}
            />
          </Block>
          <Block icon={Library} tone="data" value={<Decode text={String(n.search_hits)} />} label={`repository records for “combustion”, ${n.combustion_science} combustion science`} source={`PSI search, retrieved ${n.retrieved.slice(0, 10)} · ${n.tables} tables copied`}>
            <CellMatrix
              cell={11}
              label={`${n.combustion_science} combustion-science records and ${n.search_hits - n.combustion_science} others`}
              groups={[
                { n: n.combustion_science, color: "var(--data)", name: "combustion science" },
                { n: n.search_hits - n.combustion_science, color: "var(--dim)", name: "another research area" },
              ]}
            />
          </Block>
          <Block icon={Layers} tone="amber" value={<Decode text={String(solid.n_decided)} />} label="solid-fuel test points with a stated outcome" source="NASA/TM-20210011385; PSI-99; ICES-2024-365; ICES-2025-156; NTRS 20240007628">
            <CellMatrix
              cell={6}
              label={`${solidCount("sustained")} sustained, ${solidCount("quenched")} quenched, ${solidCount("blowoff")} blown off, ${solidCount("no_ignition")} no ignition`}
              groups={[
                { n: solidCount("sustained"), color: "var(--amber)", name: "sustained" },
                { n: solidCount("quenched") + solidCount("blowoff"), color: "var(--ext)", name: "went out (quenched or blown off)" },
                { n: solidCount("no_ignition"), color: "var(--dim)", name: "no ignition" },
              ]}
            />
          </Block>
          <Block icon={BadgeCheck} tone="done" value={<Decode text={String(n.evidence)} />} label={`sourced statements, ${n.evidence_verified} verified in full text`} source={`evidence table · ${n.evidence_index} abstract-only, ${n.evidence_unverified} not verified and marked`}>
            <CellMatrix
              label={`${n.evidence_verified} verified in full text, ${n.evidence_index} abstract only, ${n.evidence_unverified} not verified`}
              groups={[
                { n: n.evidence_verified, color: "var(--done)", name: "verified against primary source" },
                { n: n.evidence_index, color: "var(--amber)", name: "abstract or summary only" },
                { n: n.evidence_unverified, color: "var(--dim)", name: "not verified" },
              ]}
            />
          </Block>
        </div>
      </section>

      <Section title="What the droplet tests show" explainer="Oxygen, fuel, and what the word “extinction” leaves out.">
        <OverviewCharts />
      </Section>

      <Section title="The dangerous combination" explainer="Four conditions future crewed vehicles push towards at the same time.">
        <TileRow>
          <Tile icon={Thermometer} meter={0.3} value="30%+" unit="O2" tone="amber" label="expected in Moon-base and rover cabins, at 10.2 psi or less" source={ev("brief-atmospheres").source_ref} />
          <Tile icon={EyeOff} meter={cool.indicated / s.heptane_extinctions} value={`${cool.indicated} of ${s.heptane_extinctions}`} tone="ext" label="“no visible flame” was not “fire out”: a cool flame kept burning" source={`${flex.meta.report}, Appendix B captions`} />
          <Tile icon={Flame} meter={(env.o2?.[1] ?? 0) / 100} value={`${env.o2?.[1].toFixed(1)}%`} tone="data" label="highest oxygen level of any solid-fuel test point; nothing above 34%" source={`${solid.n_decided} solid-fuel test points with a stated outcome`} />
          <Tile icon={Moon} value={partialG} tone="dim" tag={<NoDataTag />} label="combustion tests in lunar or Martian gravity in the repository" source={ev("brief-no-partial-g").source_ref} />
        </TileRow>
      </Section>

      <Section title="Where to look" explainer="Each page answers one question.">
        <ul className="grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 xl:grid-cols-5">
          {PAGES.filter((p) => p.href !== "/").map((p) => (
            <li key={p.href} className="bg-surface">
              <Link href={p.href} className="group flex h-full flex-col gap-3 p-4 outline-none hover:bg-accent focus-visible:bg-accent">
                <span className="flex items-center justify-between">
                  <IconChip icon={p.icon} tone="amber" />
                  <ArrowRight aria-hidden className="size-4 text-dim transition-transform group-hover:translate-x-1 group-hover:text-amber" />
                </span>
                <span className="text-panel font-semibold text-foreground">{p.label}</span>
                <span className="text-body text-muted-foreground">{p.question}</span>
                <span className="num mt-auto text-note text-dim">{p.href}</span>
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
