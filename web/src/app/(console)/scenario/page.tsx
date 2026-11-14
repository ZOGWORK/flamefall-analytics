import type { Metadata } from "next";

import { PageHeader } from "@/components/console/primitives";
import { Lab } from "./lab";

export const metadata: Metadata = { title: "Scenario Lab" };

export default function Page() {
  return (
    <>
      <PageHeader
        kicker="Interactive · estimates, never verdicts"
        title="Scenario Lab"
        lede="Set an atmosphere, a material, a flow and a gravity level. The answer is the nearest real tests, an estimate where a model passed validation, and “no data” where nothing was measured."
      />
      <Lab />
    </>
  );
}
