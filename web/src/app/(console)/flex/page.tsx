import type { Metadata } from "next";

import { PageHeader } from "@/components/console/primitives";
import { Explorer } from "./explorer";

export const metadata: Metadata = { title: "FLEX Explorer" };

export default function Page() {
  return (
    <>
      <PageHeader
        kicker="Droplet combustion · quantitative core"
        title="FLEX Explorer"
        lede="Single droplets of methanol or n-heptane burned on the space station while the atmosphere was varied. One row per burn, as printed."
      />
      <Explorer />
    </>
  );
}
