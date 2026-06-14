"use client";

import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

const metrics = [
  {
    label: "Total Value",
    value: "₹48,75,000",
    change: "+18%",
  },
  {
    label: "Avg. Deal Value",
    value: "₹3,80,000",
    change: "+12%",
  },
  {
    label: "Conversion Rate",
    value: "21.65%",
    change: "+10%",
  },
];

export default function PipelineOverview() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#141419] border border-[#24242b] rounded-3xl p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">
          Pipeline Overview
        </h2>

        {/* Dropdown */}
        <select className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#1b1b22] border border-[#2b2b35] text-sm text-white outline-none cursor-pointer">
          <option>This Week</option>
          <option>This Month</option>
          <option>This Year</option>
          <option>Custom Range</option>
        </select>
      </div>

      <div className="space-y-5">
        {metrics.map((item, index) => (
          <div
            key={index}
            className="flex items-center justify-between border-b border-[#24242b] pb-4"
          >
            <div>
              <p className="text-sm text-gray-400">{item.label}</p>

              <h3 className="text-xl font-bold text-white mt-1">
                {item.value}
              </h3>
            </div>

            <div className="text-green-400 font-semibold text-sm">
              ↑ {item.change}
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  );
}