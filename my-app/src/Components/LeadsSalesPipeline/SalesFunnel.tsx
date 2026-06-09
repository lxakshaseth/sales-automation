"use client";

import { motion } from "framer-motion";

const stages = [
  {
    label: "New Lead",
    count: 18,
    pct: "14.06%",
    color: "#3b82f6",
    width: 100,
  },
  {
    label: "Contacted",
    count: 22,
    pct: "17.19%",
    color: "#facc15",
    width: 88,
  },
  {
    label: "Qualified",
    count: 20,
    pct: "15.62%",
    color: "#22c55e",
    width: 76,
  },
  {
    label: "Proposal",
    count: 15,
    pct: "11.72%",
    color: "#8b5cf6",
    width: 64,
  },
  {
    label: "Negotiation",
    count: 10,
    pct: "7.81%",
    color: "#f97316",
    width: 52,
  },
  {
    label: "Won",
    count: 21,
    pct: "16.41%",
    color: "#10b981",
    width: 40,
  },
  {
    label: "Lost",
    count: 10,
    pct: "7.81%",
    color: "#ef4444",
    width: 28,
  },
];

export default function SalesFunnel() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-slate-200 rounded-3xl p-6"
    >
      <h2 className="text-lg font-semibold text-slate-900 mb-6">
        Sales Pipeline Funnel
      </h2>

      <div className="flex gap-8 items-start">
        
        {/* FUNNEL */}
        <div className="flex-1 flex flex-col items-center mt-2">

          {stages.map((stage, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scaleX: 0 }}
              animate={{ opacity: 1, scaleX: 1 }}
              transition={{ delay: index * 0.08 }}
              className="relative"
              style={{
                width: `${stage.width}%`,
                height: "42px",
                background: stage.color,
                marginTop: "-4px",
                clipPath:
                  "polygon(8% 0%, 92% 0%, 100% 100%, 0% 100%)",
                transformOrigin: "center",
                borderRadius: "8px",
              }}
            />
          ))}

        </div>

        {/* RIGHT SIDE DATA */}
        <div className="space-y-5 min-w-[230px]">

          {stages.map((stage, index) => (
            <div
              key={index}
              className="flex items-center justify-between gap-4"
            >
              
              <div className="flex items-center gap-3">
                
                <div
                  className="w-3 h-3 rounded-sm"
                  style={{
                    background: stage.color,
                  }}
                />

                <span className="text-sm text-gray-200">
                  {stage.label}
                </span>
              </div>

              <div className="text-sm font-medium text-white">
                {stage.count}

                <span className="text-gray-400 ml-1">
                  ({stage.pct})
                </span>
              </div>

            </div>
          ))}

        </div>
      </div>
    </motion.div>
  );
}