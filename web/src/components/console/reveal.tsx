"use client";

import { motion } from "motion/react";

/** Content that settles in when it scrolls into view (Motion, whileInView), once. */
export function Reveal({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <motion.div className={className} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.06 }} transition={{ duration: 0.5, ease: [0.2, 0.7, 0.2, 1] }}>
      {children}
    </motion.div>
  );
}
