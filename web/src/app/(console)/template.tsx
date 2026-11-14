"use client";

import { motion } from "motion/react";

/** Each page settles in when it is navigated to. The frame around it never reloads. */
export default function Template({ children }: { children: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="stagger space-y-8">
      {children}
    </motion.div>
  );
}
