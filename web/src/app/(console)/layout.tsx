import { Sidebar, TopBar } from "@/components/shell/sidebar";

/** The console frame: a fixed rail on wide screens, a top bar with a closed menu on narrow ones. */
export default function ConsoleLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Sidebar />
      <TopBar />
      <main className="lg:pl-60">
        <div className="mx-auto w-full max-w-[1280px] px-4 pt-6 pb-16 sm:px-6 lg:px-8">{children}</div>
      </main>
    </>
  );
}
