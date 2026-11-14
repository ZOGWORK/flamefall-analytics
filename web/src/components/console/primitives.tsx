// The building blocks every page is made of. Each section follows one order:
// heading, one-line plain-English explainer, the visual, then the source footnote.

import { ArrowUpRight } from "lucide-react";

import { Decode } from "@/components/console/decode";
import { cn } from "@/lib/utils";
import type { Outcome, Verification } from "@/lib/types";

/** Numbers, test identifiers and units are always monospace with tabular figures. */
export function Num({ children, className }: { children: React.ReactNode; className?: string }) {
  return <span className={cn("num", className)}>{children}</span>;
}

const NUMBER = /(\d[\d,.]*(?:\s?(?:%|kPa|psi|psia|atm|mm\/s|cm\/s|mm²\/s|mm|cm|nm|kJ|W|K|s|g|m3|m³|RPM|ppm)(?![A-Za-z]))?)/g;

/** Running text with every number set in the monospace face. */
export function Prose({ text, className }: { text: string; className?: string }) {
  const parts = text.split(NUMBER);
  return (
    <span className={className}>
      {parts.map((part, i) => (i % 2 === 1 ? <span key={i} className="num">{part}</span> : part))}
    </span>
  );
}

export function Kicker({ children, className }: { children: React.ReactNode; className?: string }) {
  return <p className={cn("kicker text-amber", className)}>{children}</p>;
}

export function PageHeader({ kicker, title, lede }: { kicker: string; title: string; lede: string }) {
  return (
    <header className="border-b border-line pb-5">
      <Kicker>{kicker}</Kicker>
      <h1 className="mt-2 text-heading font-semibold text-foreground">{title}</h1>
      <p className="mt-2 max-w-3xl text-body text-muted-foreground">
        <Prose text={lede} />
      </p>
    </header>
  );
}

/** Provenance footnote. No number goes on screen without one of these under it. */
export function Source({
  children,
  href,
  verification,
  className,
}: {
  children: React.ReactNode;
  href?: string | null;
  verification?: Verification | string | null;
  className?: string;
}) {
  return (
    <p className={cn("mt-3 text-note text-muted-foreground", className)}>
      {verification !== undefined && <VerificationBadge level={verification} className="mr-2" />}
      <span className="text-dim">Source: </span>
      {typeof children === "string" ? <Prose text={children} /> : children}
      {href && (
        <>
          {" · "}
          <a
            href={href}
            target="_blank"
            rel="noopener"
            className="inline-flex items-baseline gap-0.5 whitespace-nowrap text-foreground underline decoration-line hover:decoration-amber"
          >
            open source
            <ArrowUpRight aria-hidden className="size-3 self-center" />
          </a>
        </>
      )}
    </p>
  );
}

/** A page section: heading, explainer, visual, source. */
export function Section({
  kicker,
  title,
  explainer,
  children,
  className,
  id,
}: {
  kicker?: string;
  title: string;
  explainer: string;
  children: React.ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={cn("border-t border-line pt-6", className)}>
      {kicker && <Kicker className="mb-2 text-dim">{kicker}</Kicker>}
      <h2 className="text-heading font-medium text-foreground">{title}</h2>
      <p className="mt-1 max-w-3xl text-body text-muted-foreground">
        <Prose text={explainer} />
      </p>
      <div className="mt-4">{children}</div>
    </section>
  );
}

/** A bordered panel inside a section, with its own title, explainer and source. */
export function Panel({
  title,
  explainer,
  children,
  className,
  aside,
}: {
  title?: string;
  explainer?: string;
  children: React.ReactNode;
  className?: string;
  aside?: React.ReactNode;
}) {
  return (
    <div className={cn("rounded-xl border border-line bg-surface p-4", className)}>
      {(title || aside) && (
        <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          {title && <h3 className="text-panel font-semibold text-foreground">{title}</h3>}
          {aside}
        </div>
      )}
      {explainer && (
        <p className="mt-1 text-body text-muted-foreground">
          <Prose text={explainer} />
        </p>
      )}
      <div className={title || explainer ? "mt-3" : undefined}>{children}</div>
    </div>
  );
}

export type Tone = "amber" | "data" | "ext" | "done" | "disrupt" | "dim";

const TONE_TEXT: Record<Tone, string> = {
  amber: "text-amber",
  data: "text-data",
  ext: "text-ext",
  done: "text-done",
  disrupt: "text-disrupt",
  dim: "text-muted-foreground",
};
const TONE_BORDER: Record<Tone, string> = {
  amber: "border-amber",
  data: "border-data",
  ext: "border-ext",
  done: "border-done",
  disrupt: "border-disrupt",
  dim: "border-dim",
};

/** A small stamped label. */
export function Tag({ children, tone = "dim", className }: { children: React.ReactNode; tone?: Tone; className?: string }) {
  return (
    <span
      className={cn(
        "kicker inline-flex items-center border px-1.5 py-px align-middle whitespace-nowrap",
        TONE_BORDER[tone],
        TONE_TEXT[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

const VERIFICATION: Record<string, [string, Tone]> = {
  verified_live: ["verified against primary source", "done"],
  index: ["abstract or summary only", "amber"],
  unverified: ["not verified", "dim"],
};

/** Anything missing or unknown reads as "not verified". */
export function VerificationBadge({ level, className }: { level?: string | null; className?: string }) {
  const [text, tone] = VERIFICATION[(level ?? "").trim()] ?? VERIFICATION.unverified;
  return (
    <Tag tone={tone} className={className}>
      {text}
    </Tag>
  );
}

export const OUTCOME_TONE: Record<Outcome, Tone> = { Extinction: "ext", Disruption: "disrupt", Completion: "done" };
export const OUTCOME_COLOR: Record<Outcome, string> = {
  Extinction: "var(--ext)",
  Disruption: "var(--disrupt)",
  Completion: "var(--done)",
};
export const FUEL_COLOR: Record<string, string> = { Methanol: "var(--data)", Heptane: "var(--amber)" };

export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  return <Tag tone={OUTCOME_TONE[outcome]}>{outcome}</Tag>;
}

/** A readout tile: one number, what it is, and where it comes from. */
export function Readout({
  value,
  unit,
  label,
  source,
  tone = "amber",
  className,
}: {
  value: React.ReactNode;
  unit?: string;
  label: string;
  source: string;
  tone?: Tone;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col border border-line bg-surface p-3", className)}>
      <p className={cn("num text-heading leading-none font-medium", TONE_TEXT[tone])}>
        {value}
        {unit && <span className="ml-1.5 text-note text-muted-foreground">{unit}</span>}
      </p>
      <p className="mt-2 text-body text-foreground">
        <Prose text={label} />
      </p>
      <p className="mt-auto pt-2 text-note text-muted-foreground">
        <Prose text={source} />
      </p>
    </div>
  );
}

export function ReadoutGrid({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("grid grid-cols-1 gap-px sm:grid-cols-2 xl:grid-cols-4 [&>*]:-m-px", className)}>{children}</div>;
}

/** The explicit NO DATA panel. "No data" is an answer, not an error. */
export function NoData({ title, children, note, className }: { title: string; children: React.ReactNode; note?: string; className?: string }) {
  return (
    <div role="note" className={cn("rounded-xl border border-dashed border-dim bg-surface p-4", className)}>
      <p className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="num bg-foreground px-1.5 py-px text-note font-bold tracking-widest text-background">NO DATA</span>
        <span className="text-panel font-semibold text-foreground">
          <Prose text={title} />
        </span>
      </p>
      <div className="mt-2 max-w-3xl text-body text-muted-foreground">{typeof children === "string" ? <Prose text={children} /> : children}</div>
      {note && (
        <p className="mt-2 text-note text-dim">
          <Prose text={note} />
        </p>
      )}
    </div>
  );
}

/** A short statement set apart by a coloured rule: red for danger, cyan for a reading note. */
export function Callout({
  title,
  children,
  tone = "amber",
  note,
  className,
}: {
  title: string;
  children: React.ReactNode;
  tone?: Tone;
  note?: string;
  className?: string;
}) {
  return (
    <div className={cn("rounded-r-xl border-l-2 bg-surface py-3 pr-4 pl-4", TONE_BORDER[tone], className)}>
      <h3 className="text-panel font-semibold text-foreground">
        <Prose text={title} />
      </h3>
      <div className="mt-1 text-body text-muted-foreground">{typeof children === "string" ? <Prose text={children} /> : children}</div>
      {note && (
        <p className="mt-2 text-note text-dim">
          <Prose text={note} />
        </p>
      )}
    </div>
  );
}

/** Label / value rows. */
export function KV({ rows, className }: { rows: [string, React.ReactNode][]; className?: string }) {
  return (
    <dl className={cn("grid grid-cols-[minmax(7rem,auto)_1fr] gap-x-4 text-body", className)}>
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="border-b border-line py-1.5 text-muted-foreground">{k}</dt>
          <dd className="border-b border-line py-1.5 text-foreground">{v}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Quote({ children }: { children: React.ReactNode }) {
  return <blockquote className="border-l border-dim pl-4 text-body text-foreground italic">{children}</blockquote>;
}

/** The top band of a page: its most important number in the biggest type, with smaller readouts beside it. */
export function HeroBand({
  kicker,
  value,
  tone = "amber",
  children,
  source,
  readouts,
}: {
  kicker: string;
  value: React.ReactNode;
  tone?: Tone;
  children: React.ReactNode;
  source: string;
  readouts: React.ReactNode;
}) {
  return (
    <section className="beam grid grid-cols-1 gap-px border border-line bg-line xl:grid-cols-12">
      <div className="scan bg-surface p-4 sm:p-5 xl:col-span-5">
        <Kicker className="text-dim">{kicker}</Kicker>
        <p className={cn("glow num mt-2 text-[clamp(3.5rem,9vw,6rem)] leading-none font-bold tracking-tight", TONE_TEXT[tone])}>
          {typeof value === "string" || typeof value === "number" ? <Decode text={String(value)} /> : value}
        </p>
        <p className="mt-3 text-body text-foreground">{children}</p>
        <p className="mt-1 text-note text-muted-foreground">
          <span className="text-dim">Source: </span>
          <Prose text={source} />
        </p>
      </div>
      <div className="grid grid-cols-1 gap-px bg-line sm:grid-cols-3 xl:col-span-7">{readouts}</div>
    </section>
  );
}

/** A number tile: the value in large type, one line saying what it is, and its source. */
export function Tile({
  value,
  unit,
  label,
  source,
  tone = "amber",
  tag,
  className,
}: {
  value: React.ReactNode;
  unit?: string;
  label: string;
  source: string;
  tone?: Tone;
  tag?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col bg-surface p-4", className)}>
      {tag && <p className="mb-2">{tag}</p>}
      <p className={cn("glow num text-[clamp(1.875rem,3.4vw,2.75rem)] leading-none font-bold tracking-tight", TONE_TEXT[tone])}>
        {typeof value === "string" || typeof value === "number" ? <Decode text={String(value)} /> : value}
        {unit && <span className="ml-1.5 text-panel font-medium text-muted-foreground">{unit}</span>}
      </p>
      <p className="mt-2 text-body text-foreground">
        <Prose text={label} />
      </p>
      <p className="mt-auto pt-2 text-note text-muted-foreground">
        <span className="text-dim">Source: </span>
        <Prose text={source} />
      </p>
    </div>
  );
}

/** A row of tiles separated by hairlines. */
export function TileRow({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 xl:grid-cols-4", className)}>{children}</div>;
}

export function NoDataTag() {
  return <span className="num bg-foreground px-1.5 py-px text-note font-bold tracking-widest text-background">NO DATA</span>;
}
