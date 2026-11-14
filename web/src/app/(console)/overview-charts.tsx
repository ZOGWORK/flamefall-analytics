"use client";

import { FuelBars } from "@/components/charts/console-charts";
import { ShareChart } from "@/components/charts/flex-charts";
import { CountBars } from "@/components/charts/unknown-charts";
import { Panel, Source } from "@/components/console/primitives";
import { flex, TABLE_SOURCE } from "@/lib/data";

/** The Overview's three pictures: oxygen against extinction, fuel against extinction, and what "extinction" hid. */
export function OverviewCharts() {
  const s = flex.summary;
  const c = s.cool_flame;
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-5">
      <Panel className="xl:col-span-3" title="Oxygen against extinction" explainer="Share of tests ending in Extinction at each tested oxygen level. Bigger dots mean more tests.">
        <ShareChart rows={flex.rows} xcol="o2_pct" />
        <Source href={flex.meta.pdf_url}>{`${TABLE_SOURCE}. Bars are 95% intervals; the dashed trend is one-variable and not a causal effect.`}</Source>
      </Panel>
      <div className="grid grid-cols-1 gap-4 xl:col-span-2">
        <Panel title="Fuel against extinction" explainer="Same apparatus, two fuels.">
          <FuelBars summary={s} />
          <Source href={flex.meta.pdf_url}>{`${TABLE_SOURCE}, recomputed from the data.`}</Source>
        </Panel>
        <Panel title={`What “Extinction” hid: ${s.heptane_extinctions} n-heptane tests`} explainer="The visible flame went out. In most, the droplet kept burning as a cool flame.">
          <CountBars
            total={s.heptane_extinctions}
            rows={[
              { label: "Cool-flame evidence", value: c.indicated, color: "var(--amber)" },
              { label: "No evidence", value: c.not_indicated, color: "var(--data)" },
              { label: "Unclear", value: c.unclear, color: "var(--dim)" },
              { label: "Caption silent", value: c[""], color: "var(--input)" },
            ]}
          />
          <Source href={flex.meta.pdf_url}>{`${flex.meta.report}, Appendix B figure captions.`}</Source>
        </Panel>
      </div>
    </div>
  );
}
