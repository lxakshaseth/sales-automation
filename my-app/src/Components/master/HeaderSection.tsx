"use client";

import { motion } from "framer-motion";

export default function HeaderSection() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-8"
    ><h1 className="text-[34px] font-bold text-[#111827]">
  Master
</h1>

<p className="text-[#6b7280] mt-[-5] text-[15px]">
  Manage all master data and lookups
</p>
    </motion.div>
  );
}