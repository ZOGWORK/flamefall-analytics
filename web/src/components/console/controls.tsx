"use client";

// Input controls shared by the interactive pages. All of them change React state only:
// nothing here navigates or reloads.

import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";

export function Field({ label, hint, children, className }: { label: string; hint?: string; children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("min-w-0", className)}>
      <Label className="kicker text-dim">{label}</Label>
      <div className="mt-1.5">{children}</div>
      {hint && <p className="mt-1 text-note text-dim">{hint}</p>}
    </div>
  );
}

export interface Option {
  value: string;
  label: string;
}

const ITEM =
  "h-7 rounded-sm border border-line px-2.5 text-body text-muted-foreground hover:bg-accent hover:text-foreground aria-pressed:border-amber aria-pressed:bg-transparent aria-pressed:text-amber data-pressed:border-amber data-pressed:bg-transparent data-pressed:text-amber";

/** Several of a set. An empty selection is allowed and means "nothing selected". */
export function Chips({ options, value, onChange, label }: { options: Option[]; value: string[]; onChange: (v: string[]) => void; label: string }) {
  return (
    <ToggleGroup multiple value={value} onValueChange={(v) => onChange(v as string[])} aria-label={label} spacing={1} className="flex-wrap">
      {options.map((o) => (
        <ToggleGroupItem key={o.value} value={o.value} className={ITEM}>
          {o.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

/** Exactly one of a set. Pressing the selected one again keeps it selected. */
export function Segments({ options, value, onChange, label }: { options: Option[]; value: string; onChange: (v: string) => void; label: string }) {
  return (
    <ToggleGroup
      value={[value]}
      onValueChange={(v) => {
        const next = (v as string[]).find((x) => x !== value);
        if (next) onChange(next);
      }}
      aria-label={label}
      spacing={1}
      className="flex-wrap"
    >
      {options.map((o) => (
        <ToggleGroupItem key={o.value} value={o.value} className={ITEM}>
          {o.label}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}

/** A two-thumb range with its current values shown in the monospace face. */
export function RangeField({
  label,
  hint,
  min,
  max,
  step,
  value,
  onChange,
  format,
}: {
  label: string;
  hint?: string;
  min: number;
  max: number;
  step: number;
  value: [number, number];
  onChange: (v: [number, number]) => void;
  format: (v: number) => string;
}) {
  return (
    <div className="min-w-0">
      <div className="flex items-baseline justify-between gap-2">
        <Label className="kicker text-dim">{label}</Label>
        <span className="num text-note text-foreground">
          {format(value[0])} – {format(value[1])}
        </span>
      </div>
      <Slider className="mt-3" min={min} max={max} step={step} value={value} onValueChange={(v) => onChange(v as unknown as [number, number])} aria-label={label} />
      {hint && <p className="mt-2 text-note text-dim">{hint}</p>}
    </div>
  );
}

/** A single value on a slider. */
export function SliderField({
  label,
  hint,
  min,
  max,
  step,
  value,
  onChange,
  format,
}: {
  label: string;
  hint?: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (v: number) => void;
  format: (v: number) => string;
}) {
  return (
    <div className="min-w-0">
      <div className="flex items-baseline justify-between gap-2">
        <Label className="kicker text-dim">{label}</Label>
        <span className="num text-panel text-amber">{format(value)}</span>
      </div>
      <Slider className="mt-3" min={min} max={max} step={step} value={value} onValueChange={(v) => onChange(v as number)} aria-label={label} />
      {hint && <p className="mt-2 text-note text-dim">{hint}</p>}
    </div>
  );
}

/** One of a longer list. */
export function Pick({
  options,
  value,
  onChange,
  label,
  className,
  mono,
}: {
  options: Option[];
  value: string;
  onChange: (v: string) => void;
  label: string;
  className?: string;
  mono?: boolean;
}) {
  return (
    <Select items={options} value={value} onValueChange={(v) => v !== null && onChange(v as string)}>
      <SelectTrigger aria-label={label} className={cn("h-8 w-full rounded-sm border-input bg-background", mono && "num", className)}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent className="rounded-sm border border-input" alignItemWithTrigger={false}>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value} className={cn("rounded-sm", mono && "num")}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
