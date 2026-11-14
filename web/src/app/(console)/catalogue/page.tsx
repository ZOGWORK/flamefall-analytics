import type { Metadata } from "next";

import { PageHeader } from "@/components/console/primitives";
import { Catalogue } from "./catalogue";

export const metadata: Metadata = { title: "Investigation Catalogue" };

export default function Page() {
  return (
    <>
      <PageHeader
        kicker="PSI Data Repository · combustion science"
        title="Investigation Catalogue"
        lede="What each experiment burned, under which conditions, and its key result. Fields the repository does not state are left blank."
      />
      <Catalogue />
    </>
  );
}
