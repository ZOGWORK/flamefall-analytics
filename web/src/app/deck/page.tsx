import type { Metadata } from "next";

import { Deck } from "./deck";

export const metadata: Metadata = {
  title: "Slide deck",
  description: "Seven slides: the problem, the core dataset, what a crew cannot see, how the intelligence layer works, and where the data stops.",
};

export default function Page() {
  return <Deck />;
}
