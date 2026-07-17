"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

type AuthPageMotionProps = {
  children: ReactNode;
  direction?: "left" | "right";
};

export default function AuthPageMotion({
  children,
  direction = "right",
}: AuthPageMotionProps) {
  return (
    <motion.div
      initial={{
        opacity: 0,
        x: direction === "right" ? 70 : -70,
        scale: 0.98,
      }}
      animate={{
        opacity: 1,
        x: 0,
        scale: 1,
      }}
      transition={{
        duration: 0.45,
        ease: [0.22, 1, 0.36, 1],
      }}
      className="w-full"
    >
      {children}
    </motion.div>
  );
}