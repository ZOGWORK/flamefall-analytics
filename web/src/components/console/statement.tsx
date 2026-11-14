import { cn } from "@/lib/utils";
import { ev } from "@/lib/data";
import type { Evidence } from "@/lib/types";
import { Prose, Source, Tag } from "./primitives";

/** One sourced statement, with its read level and verification. An unverified one is dimmed. */
export function Statement({ id, entry, lead, className }: { id?: string; entry?: Evidence; lead?: string; className?: string }) {
  const e = entry ?? ev(id as string);
  const unverified = e.verification === "unverified";
  return (
    <div className={cn("border-b border-line py-3 last:border-b-0", className)}>
      <p className={cn("text-body", unverified ? "text-muted-foreground" : "text-foreground")}>
        {lead && <span className="num mr-2 text-amber">{lead}</span>}
        {!e.o2_is_ambient && (
          <Tag tone="ext" className="mr-2">
            burner feed, not ambient
          </Tag>
        )}
        <Prose text={e.statement} />
      </p>
      <Source href={e.source_url} verification={e.verification} className="mt-1.5">
        {`${e.source_ref} · read: ${e.read_level}`}
      </Source>
    </div>
  );
}

/** Only the footnote of an evidence entry, for a chart that draws its numbers. */
export function Cite({ id }: { id: string }) {
  const e = ev(id);
  return (
    <Source href={e.source_url} verification={e.verification}>
      {`${e.source_ref} · read: ${e.read_level}`}
    </Source>
  );
}
