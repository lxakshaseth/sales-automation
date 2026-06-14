"use client";

import { motion } from "framer-motion";
import {
  Bot,
  MoreVertical,
} from "lucide-react";

const settings = [
  {
    name: "AI Lead Scoring",
    enabled: true,
  },
  {
    name: "AI Reply Suggestions",
    enabled: true,
  },
  {
    name: "AI Sentiment Analysis",
    enabled: true,
  },
  {
    name: "Auto Deal Prediction",
    enabled: false,
  },
  {
    name: "AI Lead Qualification",
    enabled: true,
  },
];

export default function AIConfiguration() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white border border-[#e8edf4] rounded-[22px] p-5 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#e8f8ee] flex items-center justify-center">
            <Bot
              size={22}
              className="text-[#16a34a]"
            />
          </div>

          <div>
            <h2 className="text-[20px] font-bold text-[#111827]">
              AI Configuration
            </h2>

            <p className="text-[13px] text-[#64748b] mt-1">
              Manage AI behaviour and automation intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="h-10 px-5 rounded-xl border border-[#d8b4fe] text-[#8b5cf6] text-sm font-medium bg-white">
            Save Configuration
          </button>

          <button className="w-10 h-10 rounded-xl border border-[#e5e7eb] flex items-center justify-center">
            <MoreVertical
              size={16}
              className="text-gray-500"
            />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="border border-[#edf2f7] rounded-2xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-[#f8fafc] border-b border-[#edf2f7]">
              <th className="text-left px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Setting
              </th>

              <th className="text-center px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Status
              </th>
            </tr>
          </thead>

          <tbody>
            {settings.map((item, index) => (
              <tr
                key={index}
                className="border-b border-[#edf2f7] last:border-b-0"
              >
                <td className="px-5 h-[46px] text-[14px] text-[#111827]">
                  {item.name}
                </td>

                <td className="px-5 h-[46px] text-center">
                  <div
                    className={`w-8 h-5 rounded-full mx-auto relative transition-all ${
                      item.enabled
                        ? "bg-[#22c55e]"
                        : "bg-[#d1d5db]"
                    }`}
                  >
                    <div
                      className={`absolute top-[2px] w-4 h-4 bg-white rounded-full transition-all ${
                        item.enabled
                          ? "right-[2px]"
                          : "left-[2px]"
                      }`}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-4">
        <p className="text-[13px] text-[#64748b]">
          Showing 5 AI settings
        </p>
      </div>
    </motion.div>
  );
}