import { EyeOff, Flame, FlaskConical, Moon, Orbit, Radar, Siren, Thermometer, Wind } from "lucide-react";
import type { Metadata } from "next";

import { CountBars, DiluentChart, LuciChart, SolidEnvelopeChart } from "@/components/charts/unknown-charts";
import { EvidenceGroup } from "@/components/console/evidence-group";
import { HeroBand, NoData, NoDataTag, PageHeader, Panel, Prose, Quote, Readout, Section, Source, Tile, TileRow } from "@/components/console/primitives";
import { partialGravityRecords } from "@/lib/catalogue";
import { catalogue, ev, flex, panels, solid, SOLID_O2_LIMIT } from "@/lib/data";
import { SmokeTabs } from "./smoke-tabs";

export const metadata: Metadata = { title: "What We Don't Know" };

export default function Page() {
  const s = flex.summary;
  const c = s.cool_flame;
  const env = solid.envelope_all;
  const decided = solid.points.filter((p) => p.outcome !== "ambiguous");
  const partialG = partialGravityRecords(catalogue.investigations).length;
  const aboveLimit = decided.filter((p) => (p.o2_at_outcome_pct ?? 0) > SOLID_O2_LIMIT).length;
  const luci = panels.luci.rows;
  const kapton = panels.smoke.flights[0].rows[0];
  const alarm = ev("saffire-alarm-981");
  const delta = ev("lunar-g-centrifuge-delta");
  const highest = (points: typeof decided) => points.reduce((a, b) => ((b.o2_at_outcome_pct ?? 0) > (a.o2_at_outcome_pct ?? 0) ? b : a));
  const top = highest(decided);
  const topSustained = highest(decided.filter((p) => p.outcome === "sustained"));

  return (
    <>
      <PageHeader kicker="Honest limits" title="What We Don't Know" lede="Where the measurements stop, and the kinds of burning a crew or a sensor can miss." />

      <HeroBand
        kicker="Partial-gravity tests in the repository"
        value={partialG}
        tone="amber"
        source="official challenge brief, Flame in Freefall; PSI Data Repository search “combustion”"
        readouts={
          <>
            <Readout className="border-0" icon={Thermometer} meter={(env.o2?.[1] ?? 0) / 100} tone="amber" value={`${env.o2?.[1].toFixed(1)}%`} label="highest oxygen of any solid-fuel test point" source={`${decided.length} test points with a stated outcome`} />
            <Readout className="border-0" icon={FlaskConical} meter={s.co2_and_he / s.n} tone="data" value={`${s.co2_and_he} of ${s.n}`} label="droplet tests with both CO2 and helium" source={`${flex.meta.report}, Table IX`} />
            <Readout className="border-0" icon={EyeOff} meter={c.indicated / s.heptane_extinctions} tone="ext" value={`${c.indicated} of ${s.heptane_extinctions}`} label="n-heptane “extinctions” that kept burning" source={`${flex.meta.report}, Appendix B captions`} />
          </>
        }
      >
        combustion tests in lunar or Martian gravity. Every flight investigation in the catalogue ran in microgravity.
      </HeroBand>

      <Section kicker="Gap 1" title="Partial gravity" explainer="No repository dataset. The nearest real evidence is one suborbital flight and a few short ground tests.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-3" title="Spread rate: simulated lunar gravity against normal gravity" explainer="One flight, preliminary slides. Lunar gravity came from spinning the capsule, so Coriolis force affects the flames.">
            <LuciChart rows={luci} unit={panels.luci.unit} />
            <Source href={panels.luci.source_url} verification={panels.luci.verification}>
              {`${panels.luci.source_ref}. The PMMA values are printed as 0.15 and 0.40 cm/s.`}
            </Source>
          </Panel>
          <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-3 xl:col-span-2 xl:grid-cols-1">
            <Tile icon={Moon} value={partialG} tone="dim" tag={<NoDataTag />} label="lunar- or Martian-gravity combustion datasets in the repository" source="official challenge brief, Flame in Freefall" />
            <Tile icon={Orbit} meter={luci[0].lunar / luci[0].earth} value={luci[0].lunar} unit={panels.luci.unit} tone="amber" label={`fabric flame-base spread in simulated lunar gravity, against ${luci[0].earth} mm/s in normal gravity`} source={`ASGSR 2025 presentation, slides ${luci[0].slides} (NTRS 20250010653)`} />
            <Tile icon={Radar} value={delta.value} unit="% O2" tone="data" label="worst-case shift in flammability limit between normal and lunar gravity, five materials at 8.2 psia" source={delta.source_ref} />
          </div>
        </div>
        <div className="mt-4">
          <Quote>
            <Prose text={panels.partial_gravity_wording} />
          </Quote>
        </div>
        <div className="mt-4">
          <EvidenceGroup ids={["lunar-g-centrifuge-delta", "partial-g-kc135", "partial-g-wires", "buoyant-velocity-unknown", "luci-method", "buoyant-velocity-ices2019"]} label="sourced statements on partial gravity" />
        </div>
        <div className="mt-3">
          <EvidenceGroup ids={["fm2-plan"]} label="sourced statement on an experiment that is planned, not flown: a plan, not evidence" />
        </div>
      </Section>

      <Section kicker="Gap 2" title="Solid materials above the tested oxygen range" explainer="Each mark is one test point. The shaded band has no test; the dashed box is where future cabins are expected to sit.">
        <Panel>
          <SolidEnvelopeChart points={decided} limit={SOLID_O2_LIMIT} />
          <Source href="https://ntrs.nasa.gov/citations/20210011385">
            {`${decided.length} solid-fuel test points with a stated outcome: NASA/TM-20210011385 (BASS-II), PSI-99 table, Olson et al. 2023, ICES-2024-365, ICES-2025-156, NTRS 20240007628. Solid fuels only; droplet and gas tests are not on this chart. ${solid.n_total - solid.n_pressure_stated} of the ${solid.n_total} points have an assumed pressure: ${solid.pressure_note}`}
          </Source>
        </Panel>
        <TileRow className="mt-4 xl:grid-cols-3">
          <Tile icon={Flame} value={aboveLimit} tone="dim" tag={<NoDataTag />} label={`solid-material test points above ${SOLID_O2_LIMIT}% oxygen, at any pressure`} source={`${decided.length} solid-fuel test points`} />
          <Tile value={`${top.o2_at_outcome_pct?.toFixed(1)}%`} tone="data" label={`highest oxygen with a recorded outcome: ${top.investigation_id} ${top.material_class}, ${top.outcome.replace("_", " ")}`} source={top.source_ref} />
          <Tile value={`${topSustained.o2_at_outcome_pct?.toFixed(1)}%`} tone="amber" label={`highest oxygen with a sustained flame: ${topSustained.investigation_id} ${topSustained.material_class} at ${topSustained.pressure_kPa?.toFixed(1)} kPa`} source={topSustained.source_ref} />
        </TileRow>
        <div className="mt-4">
          <EvidenceGroup ids={["sofie-gel-envelope", "saffire-vi-partial-pressure"]} label="sourced statements on the tested envelope" />
        </div>
      </Section>

      <Section kicker="Gap 3" title="Carbon dioxide and helium together" explainer="Every FLEX test lies on one of the two axes. The two diluents were never combined.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-3">
            <DiluentChart rows={flex.rows} both={s.co2_and_he} />
            <Source href={flex.meta.pdf_url}>{`${flex.meta.report}, Table IX.`}</Source>
          </Panel>
          <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-3 xl:col-span-2 xl:grid-cols-1">
            <Tile icon={FlaskConical} value={s.co2_and_he} tone="dim" tag={<NoDataTag />} label={`of ${s.n} tests contain both gases`} source={`${flex.meta.report}, Table IX`} />
            <Tile icon={Wind} meter={s.co2_tests / s.n} value={s.co2_tests} tone="data" label="tests with carbon dioxide" source={`${flex.meta.report}, Table IX`} />
            <Tile icon={Wind} meter={s.he_tests / s.n} value={s.he_tests} tone="data" label="tests with helium, at their own oxygen levels and pressures: its effect is unclear" source={`${flex.meta.report}, Table IX`} />
          </div>
        </div>
      </Section>

      <Section kicker="What you can't see · 1" title="Cool flames after the visible flame is gone" explainer="“Extinction” in the table means the visible flame. For n-heptane, the droplet often kept vaporising.">
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-3" title={`n-Heptane tests logged as Extinction (n = ${s.heptane_extinctions})`}>
            <CountBars
              total={s.heptane_extinctions}
              rows={[
                { label: "Cool-flame evidence", value: c.indicated, color: "var(--amber)" },
                { label: "No evidence", value: c.not_indicated, color: "var(--data)" },
                { label: "Unclear", value: c.unclear, color: "var(--dim)" },
                { label: "Caption silent", value: c[""], color: "var(--input)" },
              ]}
            />
            <Source href={flex.meta.pdf_url}>
              {`${flex.meta.report}, Appendix B figure captions: the authors' reading of continued vaporisation and a vapour cloud after the visible flame vanished. No methanol caption mentions a cool flame.`}
            </Source>
          </Panel>
          <div className="border border-line xl:col-span-2">
            <Tile icon={EyeOff} meter={c.indicated / s.heptane_extinctions} value={`${c.indicated} of ${s.heptane_extinctions}`} tone="ext" label="kept vaporising after the flame disappeared. “No visible flame” is not “fire out”" source={`${flex.meta.report}, Appendix B captions`} className="h-full" />
          </div>
        </div>
        <div className="mt-4">
          <EvidenceGroup ids={["cfig-cool-flames-psi", "flex-k-hot-cool"]} label="sourced statements on cool flames" />
        </div>
      </Section>

      <Section kicker="What you can't see · 2" title="Smoke too fine for the detector" explainer={`Geometric mean particle diameter by material, fresh and after 720 s, against the ${panels.smoke.threshold_nm} ${panels.smoke.unit} mark.`}>
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
          <Panel className="xl:col-span-3">
            <SmokeTabs />
            <p className="mt-3 text-note text-muted-foreground">{panels.smoke.note}</p>
          </Panel>
          <div className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-3 xl:col-span-2 xl:grid-cols-1">
            <Tile icon={Siren} value="½ · ⅔" tone="ext" label="of Kapton and of Teflon smoke tests in which the station-type detector did not alarm" source={ev("same-detector-misses").source_ref} />
            <Tile icon={Radar} meter={kapton.fresh / panels.smoke.threshold_nm} value={kapton.fresh} unit={panels.smoke.unit} tone="data" label={`fresh Kapton smoke, against a ${panels.smoke.threshold_nm} nm mark`} source={ev("same1-table1").source_ref} />
            <Tile icon={Siren} value={alarm.value} unit="s" tone="amber" label="for a far-field detector to reach its alarm threshold in a vehicle-scale burn" source={alarm.source_ref} />
          </div>
        </div>
        <div className="mt-4">
          <EvidenceGroup ids={["same-detector-misses", "same1-lag-qualitative", "saffire-alarm-981", "saffire-2026-alarm"]} label="sourced statements on smoke and detection" />
        </div>
      </Section>

      <Section kicker="What you can't see · 3" title="Dim blue flames, and an oxygen figure that is not a cabin" explainer="Near its limit a flame shrinks and turns blue. And 85% O2 in the tables is a burner feed, never an ambient.">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Panel title="Near the limit, in the solid-fuel tests">
            <Quote>{panels.blue_flame_quote.quote}</Quote>
            <Source href={panels.blue_flame_quote.source_url} verification={panels.blue_flame_quote.verification}>
              {panels.blue_flame_quote.source_ref}
            </Source>
          </Panel>
          <EvidenceGroup ids={["bre-21pct-out", "bre-25pct", "inverse-flame-85"]} label="sourced statements on low-flow flames and burner-feed oxygen" />
        </div>
      </Section>

      <Section title="Other gaps found while checking sources" explainer="A number that is quoted but could not be found, or a table that is not open.">
        <ul className="border border-line">
          {panels.other_gaps.map((gap) => (
            <li key={gap.gap} className="grid grid-cols-1 gap-x-6 gap-y-1 border-b border-line px-4 py-2.5 last:border-b-0 lg:grid-cols-[1fr_1.4fr]">
              <p className="text-body text-foreground">
                <Prose text={gap.gap} />
              </p>
              <div>
                <p className="text-body text-muted-foreground">
                  <Prose text={gap.status} />
                </p>
                <p className="mt-0.5 text-note text-dim">
                  Source: <Prose text={gap.source} />
                </p>
              </div>
            </li>
          ))}
        </ul>
      </Section>

      <NoData title="Nothing on this page is filled in" note={`${ev("brief-atmospheres").statement} Nothing in this data set speaks to the spacesuit condition. Source: ${ev("brief-atmospheres").source_ref}.`}>
        Every gap above is shown as a gap. No value is interpolated, scaled for gravity, or carried from one kind of fuel to another.
      </NoData>
    </>
  );
}
