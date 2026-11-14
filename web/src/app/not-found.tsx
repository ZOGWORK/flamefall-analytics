import Link from "next/link";

import { PAGES } from "@/components/shell/nav";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col justify-center px-4 py-16">
      <p className="kicker text-amber">Flamefall Analytics</p>
      <h1 className="mt-2 text-heading font-semibold text-foreground">This page does not exist</h1>
      <p className="mt-2 text-body text-muted-foreground">The address matches none of the pages of this console. They are:</p>
      <ul className="mt-4 border border-line">
        {PAGES.map((p) => (
          <li key={p.href} className="border-b border-line last:border-b-0">
            <Link href={p.href} className="block px-4 py-2.5 text-body text-foreground outline-none hover:bg-accent focus-visible:bg-accent">
              {p.label}
              <span className="ml-3 text-muted-foreground">{p.question}</span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
