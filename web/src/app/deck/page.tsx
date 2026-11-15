import type { Metadata } from "next";

import { Deck } from "./deck";

export const metadata: Metadata = {
  title: "Slide deck",
  description: "Seven slides, the same as the PowerPoint file: the problem, the FLEX evidence base, fuel against atmosphere, what extinction hides, the model and the Scenario Lab, and where the measurements stop.",
};

export default function Page() {
  return <Deck />;
}
