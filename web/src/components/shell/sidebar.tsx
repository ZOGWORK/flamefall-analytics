"use client";

import { motion } from "framer-motion";
import { Menu } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { cn } from "@/lib/utils";
import { DECK, DISCLAIMER, PAGES, REPO_URL, samePath, type NavItem } from "./nav";

function Wordmark() {
  return (
    <Link href="/" className="block leading-none">
      <span className="font-heading text-panel font-bold tracking-[0.18em] text-foreground">FLAMEFALL</span>
      <span className="kicker mt-1 block text-muted-foreground">Analytics</span>
    </Link>
  );
}

function NavLink({ item, active, onNavigate, marker }: { item: NavItem; active: boolean; onNavigate?: () => void; marker: string }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={cn(
        "relative flex items-center gap-2.5 py-2 pr-3 pl-4 text-body transition-colors outline-none focus-visible:bg-accent",
        active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
      )}
    >
      {active && <motion.span layoutId={marker} className="absolute inset-y-1 left-0 w-0.5 bg-amber shadow-[0_0_14px_2px_rgba(255,140,26,0.9)]" />}
      {active && <span aria-hidden className="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,140,26,0.14),transparent_70%)]" />}
      <Icon aria-hidden className={cn("relative size-4 shrink-0", active ? "text-amber" : "text-dim")} strokeWidth={1.75} />
      <span className={cn("relative", active && "font-medium")}>{item.label}</span>
    </Link>
  );
}

function NavList({ onNavigate, marker }: { onNavigate?: () => void; marker: string }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Pages" className="flex flex-col">
      <p className="kicker px-4 pb-1.5 text-dim">Console</p>
      {PAGES.map((item) => (
        <NavLink key={item.href} item={item} active={samePath(pathname, item.href)} onNavigate={onNavigate} marker={marker} />
      ))}
      <p className="kicker px-4 pt-5 pb-1.5 text-dim">Briefing</p>
      <NavLink item={DECK} active={samePath(pathname, DECK.href)} onNavigate={onNavigate} marker={marker} />
    </nav>
  );
}

function Fineprint() {
  return (
    <div className="space-y-3 px-4 text-note text-muted-foreground">
      <p>{DISCLAIMER}</p>
      <p>
        Not affiliated with or endorsed by NASA.{" "}
        <a href={REPO_URL} target="_blank" rel="noopener" className="text-foreground underline decoration-line">
          Code and data
        </a>
      </p>
    </div>
  );
}

/** Fixed rail on wide screens. */
export function Sidebar() {
  return (
    <aside className="glass-rail fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-line lg:flex">
      <div className="border-b border-line px-4 py-4">
        <Wordmark />
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <NavList marker="nav-rail" />
      </div>
      <div className="border-t border-line py-4">
        <Fineprint />
      </div>
    </aside>
  );
}

/** Top bar on narrow screens. The menu is closed until asked for, and closes again on navigation. */
export function TopBar() {
  const [open, setOpen] = useState(false);
  return (
    <header className="glass-rail sticky top-0 z-30 flex h-12 items-center justify-between border-b border-line px-4 lg:hidden">
      <Wordmark />
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger render={<Button variant="outline" size="icon" aria-label="Open the page menu" />}>
          <Menu aria-hidden className="size-4" />
        </SheetTrigger>
        <SheetContent side="left" className="w-72 gap-0 border-line bg-background p-0">
          <SheetHeader className="border-b border-line px-4 py-4">
            <SheetTitle className="font-heading text-panel tracking-[0.18em]">FLAMEFALL</SheetTitle>
            <SheetDescription className="text-note">Six pages, each answering one question.</SheetDescription>
          </SheetHeader>
          <div className="flex-1 overflow-y-auto py-4">
            <NavList marker="nav-sheet" onNavigate={() => setOpen(false)} />
          </div>
          <div className="border-t border-line py-4">
            <Fineprint />
          </div>
        </SheetContent>
      </Sheet>
    </header>
  );
}
