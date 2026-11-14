// Small instruments that show a value instead of describing it: a dial, a segmented meter,
// a matrix of lit cells and an icon chip. Pure SVG and CSS, so they render without a script
// and animate with CSS only. Each one carries a text alternative with the real value.

import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export type VizTone = "amber" | "data" | "ext" | "done" | "disrupt" | "dim";

export const TONE_VAR: Record<VizTone, string> = {
  amber: "var(--amber)",
  data: "var(--data)",
  ext: "var(--ext)",
  done: "var(--done)",
  disrupt: "var(--disrupt)",
  dim: "var(--dim)",
};

const clamp01 = (v: number) => (Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : 0);

/** A 270-degree dial. `value` and `tick` are fractions of the full scale. */
export function Dial({
  value,
  tone = "amber",
  size = 132,
  tick,
  label,
  children,
  className,
}: {
  value: number;
  tone?: VizTone;
  size?: number;
  tick?: number;
  label: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const r = 52;
  const arc = 0.75 * 2 * Math.PI * r; // 270 degrees
  const v = clamp01(value);
  const color = TONE_VAR[tone];
  const angle = (f: number) => ((135 + 270 * clamp01(f)) * Math.PI) / 180;
  const marks = Array.from({ length: 28 }, (_, i) => i / 27);
  return (
    <div className={cn("relative shrink-0", className)} style={{ width: size, height: size }} role="img" aria-label={label}>
      <svg viewBox="0 0 132 132" className="size-full overflow-visible">
        {marks.map((f) => (
          <line
            key={f}
            x1={66 + 62 * Math.cos(angle(f))}
            y1={66 + 62 * Math.sin(angle(f))}
            x2={66 + (f <= v ? 66 : 64.5) * Math.cos(angle(f))}
            y2={66 + (f <= v ? 66 : 64.5) * Math.sin(angle(f))}
            stroke={f <= v ? color : "var(--dim)"}
            strokeOpacity={f <= v ? 0.9 : 0.45}
            strokeWidth={1.2}
          />
        ))}
        <circle cx="66" cy="66" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="8" strokeLinecap="round" strokeDasharray={`${arc} 999`} transform="rotate(135 66 66)" />
        <circle
          cx="66"
          cy="66"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${arc * v} 999`}
          transform="rotate(135 66 66)"
          className="dial-arc"
          style={{ filter: `drop-shadow(0 0 7px ${color})`, ["--arc" as string]: `${arc * v}` }}
        />
        {tick !== undefined && (
          <line
            x1={66 + 42 * Math.cos(angle(tick))}
            y1={66 + 42 * Math.sin(angle(tick))}
            x2={66 + 61 * Math.cos(angle(tick))}
            y2={66 + 61 * Math.sin(angle(tick))}
            stroke="var(--foreground)"
            strokeWidth={1.5}
          />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">{children}</div>
    </div>
  );
}

/** A row of segments, lit up to the value. For anything that is a share or a score from 0 to 1. */
export function Meter({
  value,
  tone = "amber",
  segments = 24,
  label,
  className,
}: {
  value: number;
  tone?: VizTone;
  segments?: number;
  label: string;
  className?: string;
}) {
  const lit = Math.round(clamp01(value) * segments);
  const color = TONE_VAR[tone];
  return (
    <div className={cn("flex h-2.5 gap-[2px]", className)} role="img" aria-label={label}>
      {Array.from({ length: segments }, (_, i) => (
        <span
          key={i}
          className={cn("min-w-0 flex-1 rounded-[1px]", i < lit && "cell")}
          style={i < lit ? { background: color, boxShadow: `0 0 8px ${color}`, animationDelay: `${i * 22}ms` } : { background: "rgba(255,255,255,0.07)" }}
        />
      ))}
    </div>
  );
}

/** One cell per item, coloured by group, in the order given. Counts are shown as they are. */
export function CellMatrix({
  groups,
  label,
  cell = 9,
  className,
}: {
  groups: { n: number; color: string; name: string }[];
  label: string;
  cell?: number;
  className?: string;
}) {
  const cells = groups.flatMap((g) => Array.from({ length: g.n }, () => g));
  return (
    <div className={cn("grid gap-[3px]", className)} style={{ gridTemplateColumns: `repeat(auto-fill, minmax(${cell}px, 1fr))` }} role="img" aria-label={label}>
      {cells.map((g, i) => (
        <span key={i} title={g.name} className="cell aspect-square rounded-[2px]" style={{ background: g.color, boxShadow: `0 0 6px ${g.color}`, animationDelay: `${Math.min(i * 9, 900)}ms` }} />
      ))}
    </div>
  );
}

/** An icon on a small lit plate. */
export function IconChip({ icon: Icon, tone = "amber", className }: { icon: LucideIcon; tone?: VizTone; className?: string }) {
  const color = TONE_VAR[tone];
  return (
    <span
      aria-hidden
      className={cn("inline-flex size-8 shrink-0 items-center justify-center rounded-md border", className)}
      style={{
        color,
        borderColor: `color-mix(in srgb, ${color} 45%, transparent)`,
        background: `color-mix(in srgb, ${color} 12%, transparent)`,
        boxShadow: `0 0 18px -4px ${color}, inset 0 1px 0 rgba(255,255,255,0.12)`,
      }}
    >
      <Icon className="size-4" strokeWidth={1.75} />
    </span>
  );
}

/** A block that shows one value with an instrument: icon, number, picture, one line, source. */
export function Block({
  icon,
  tone = "amber",
  value,
  unit,
  label,
  source,
  children,
  className,
}: {
  icon: LucideIcon;
  tone?: VizTone;
  value: React.ReactNode;
  unit?: string;
  label: string;
  source: string;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col bg-surface p-4", className)}>
      <div className="flex items-start justify-between gap-3">
        <p className="glow num text-[clamp(1.5rem,2.6vw,2.125rem)] leading-none font-bold tracking-tight" style={{ color: TONE_VAR[tone] }}>
          {value}
          {unit && <span className="ml-1.5 text-note font-medium text-muted-foreground">{unit}</span>}
        </p>
        <IconChip icon={icon} tone={tone} />
      </div>
      <p className="mt-2 text-body text-foreground">{label}</p>
      {children && <div className="mt-3">{children}</div>}
      <p className="mt-auto pt-3 text-note text-muted-foreground">
        <span className="text-dim">Source: </span>
        {source}
      </p>
    </div>
  );
}
