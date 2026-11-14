"use client";

import { SmokeChart } from "@/components/charts/unknown-charts";
import { Cite } from "@/components/console/statement";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { panels } from "@/lib/data";

/** The two smoke flights stay two tables: one tab each, never averaged. */
export function SmokeTabs() {
  const { flights, threshold_nm, unit } = panels.smoke;
  return (
    <Tabs defaultValue={flights[0].id}>
      <TabsList className="h-8 max-w-full rounded-sm">
        {flights.map((f) => (
          <TabsTrigger key={f.id} value={f.id} className="rounded-sm px-3">
            {f.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {flights.map((f) => (
        <TabsContent key={f.id} value={f.id} className="mt-4">
          <SmokeChart rows={f.rows} threshold={threshold_nm} unit={unit} />
          <Cite id={f.evidence_id} />
        </TabsContent>
      ))}
    </Tabs>
  );
}
