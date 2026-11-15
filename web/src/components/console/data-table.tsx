"use client";

import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { memo, useMemo, useState } from "react";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DASH } from "@/lib/format";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  /** What to sort by. Leave out for a column that cannot be sorted. */
  sort?: (row: T) => number | string | null;
  cell: (row: T) => React.ReactNode;
  numeric?: boolean;
  title?: string;
  className?: string;
}

/** Number cell: monospace; a missing value prints as a dash, never as 0. */
export function n(value: number | null | undefined, digits = 2): React.ReactNode {
  return value === null || value === undefined || Number.isNaN(value) ? <span className="text-dim">{DASH}</span> : value.toFixed(digits);
}

function RowCells<T>({ row, columns }: { row: T; columns: Column<T>[] }) {
  return (
    <TableRow className="border-line hover:bg-accent">
      {columns.map((c) => (
        <TableCell key={c.key} className={cn("px-2.5 py-1.5 align-top", c.numeric && "num text-right whitespace-nowrap", c.className)}>
          {c.cell(row)}
        </TableCell>
      ))}
    </TableRow>
  );
}
/** One row. It renders again only when its row or the column list changes, so narrowing a filter does not redraw the rows that stay. */
const Row = memo(RowCells) as typeof RowCells;

/**
 * A sortable table. Sorting happens in the browser. Empty cells are empty in the source and stay
 * empty here; they always sort to the end.
 */
export function DataTable<T>({
  rows,
  columns,
  rowKey,
  maxHeight = 420,
  caption,
  minWidth,
}: {
  rows: T[];
  columns: Column<T>[];
  rowKey: (row: T) => string;
  maxHeight?: number;
  caption: string;
  minWidth?: number;
}) {
  const [sort, setSort] = useState<{ key: string; dir: 1 | -1 } | null>(null);

  const sorted = useMemo(() => {
    if (!sort) return rows;
    const col = columns.find((c) => c.key === sort.key);
    if (!col?.sort) return rows;
    const get = col.sort;
    return [...rows].sort((a, b) => {
      const va = get(a);
      const vb = get(b);
      if (va === null || va === "") return vb === null || vb === "" ? 0 : 1;
      if (vb === null || vb === "") return -1;
      return (va < vb ? -1 : va > vb ? 1 : 0) * sort.dir;
    });
  }, [rows, columns, sort]);

  return (
    <div className="overflow-auto rounded-xl border border-line bg-surface" style={{ maxHeight }} tabIndex={0} role="region" aria-label={caption}>
      <Table className="text-body" style={minWidth ? { minWidth } : undefined}>
        <caption className="sr-only">{caption}</caption>
        <TableHeader className="sticky top-0 z-10 bg-secondary">
          <TableRow className="border-line hover:bg-transparent">
            {columns.map((c) => {
              const active = sort?.key === c.key;
              const Icon = !active ? ChevronsUpDown : sort.dir === 1 ? ArrowUp : ArrowDown;
              return (
                <TableHead
                  key={c.key}
                  title={c.title}
                  aria-sort={active ? (sort.dir === 1 ? "ascending" : "descending") : undefined}
                  className={cn("kicker h-8 px-2.5 whitespace-nowrap text-muted-foreground", c.numeric && "text-right")}
                >
                  {c.sort ? (
                    <button
                      type="button"
                      onClick={() => setSort(active ? (sort.dir === 1 ? { key: c.key, dir: -1 } : null) : { key: c.key, dir: 1 })}
                      className={cn("kicker inline-flex items-center gap-1 outline-none hover:text-foreground focus-visible:text-amber", active && "text-amber")}
                    >
                      {c.header}
                      <Icon aria-hidden className="size-3" />
                    </button>
                  ) : (
                    c.header
                  )}
                </TableHead>
              );
            })}
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((row) => (
            <Row key={rowKey(row)} row={row} columns={columns} />
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
