import type { Metadata } from "next";

import { PageHeader } from "@/components/console/primitives";
import { ModelLab } from "./lab";

export const metadata: Metadata = { title: "Model Lab" };

export default function Page() {
  return (
    <>
      <PageHeader
        kicker="Validation · grouped cross-validation, seed 42"
        title="Model Lab"
        lede="Three small logistic models, each tested on groups it never saw. Droplet and solid data are never pooled. One fails, and is shown failing."
      />
      <ModelLab />
    </>
  );
}
