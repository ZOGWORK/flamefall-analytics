"use client";

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { ev } from "@/lib/data";
import type { Evidence } from "@/lib/types";
import { Statement } from "./statement";

/**
 * Sourced statements folded behind their count, so a page shows numbers and charts first.
 * Nothing is hidden for good: one press opens every statement with its source and read level.
 */
export function EvidenceGroup({ ids, entries, label = "sourced statements", lead = false }: { ids?: string[]; entries?: Evidence[]; label?: string; lead?: boolean }) {
  const list = entries ?? (ids ?? []).map(ev);
  if (list.length === 0) return null;
  return (
    <Accordion className="rounded-xl border border-line bg-surface">
      <AccordionItem value="evidence" className="px-4">
        <AccordionTrigger className="rounded-sm py-2.5 hover:no-underline">
          <span className="text-body font-normal text-muted-foreground">
            <span className="num mr-2 text-panel font-medium text-amber">{list.length}</span>
            {label}, each with its source and read level
          </span>
        </AccordionTrigger>
        <AccordionContent>
          {list.map((e) => (
            <Statement key={e.id} entry={e} lead={lead ? e.investigation_id : undefined} />
          ))}
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
