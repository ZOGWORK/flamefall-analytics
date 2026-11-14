"use client";

import { MotionConfig } from "framer-motion";

/** One motion setting for the whole app: quick, and off for readers who ask for reduced motion. */
export function Motion({ children }: { children: React.ReactNode }) {
  return (
    <MotionConfig reducedMotion="user" transition={{ duration: 0.28, ease: [0.2, 0, 0, 1] }}>
      {children}
    </MotionConfig>
  );
}
