import { CircleHelp, Droplets, FlaskConical, Gauge, Library, Presentation, SlidersHorizontal, type LucideIcon } from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  question: string;
  icon: LucideIcon;
}

/** The six pages. Each answers one question. */
export const PAGES: NavItem[] = [
  { href: "/", label: "Overview", question: "What was measured, in four numbers?", icon: Gauge },
  { href: "/flex/", label: "FLEX Explorer", question: "What happened in each of the 276 droplet burns?", icon: Droplets },
  { href: "/catalogue/", label: "Investigation Catalogue", question: "Which experiments matter for my vehicle?", icon: Library },
  { href: "/scenario/", label: "Scenario Lab", question: "What is the nearest real test to my scenario?", icon: SlidersHorizontal },
  { href: "/models/", label: "Model Lab", question: "How far can a model be trusted here?", icon: FlaskConical },
  { href: "/unknowns/", label: "What We Don't Know", question: "Where does the data stop?", icon: CircleHelp },
];

export const DECK: NavItem = { href: "/deck/", label: "Slide deck", question: "The seven-slide summary", icon: Presentation };

export const DISCLAIMER =
  "Estimates only. This dashboard reports what experiments measured and where no data exists. It never rates a material, atmosphere or design as acceptable for flight.";

export const REPO_URL = "https://github.com/ZOGWORK/flamefall-analytics";

/** "/flex/" and "/flex" are the same page. */
export function samePath(a: string, b: string): boolean {
  const norm = (p: string) => (p.length > 1 && p.endsWith("/") ? p.slice(0, -1) : p);
  return norm(a) === norm(b);
}
