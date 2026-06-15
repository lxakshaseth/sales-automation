"use client";

import { motion } from "framer-motion";

import {
  Globe,
  Plus,
  MoreVertical,
} from "lucide-react";

const data = [
  {
    source: "Website",
    type: "Online",
    leads: 120,
  },
  {
    source: "Facebook Ads",
    type: "Online",
    leads: 95,
  },
  {
    source: "LinkedIn",
    type: "Online",
    leads: 68,
  },
  {
    source: "Referral",
    type: "Offline",
    leads: 45,
  },
  {
    source: "Walk-in",
    type: "Offline",
    leads: 32,
  },
];

export default function LeadSources() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-[#ececf2] rounded-3xl p-7 shadow-sm"
    >
      {/* TOP */}
      <div className="flex items-start justify-between">
        
        <div className="flex items-start gap-4">
          
          <div className="w-14 h-14 rounded-2xl bg-blue-100 flex items-center justify-center">
            <Globe
              size={24}
              className="text-blue-600"
            />
          </div>

          <div>
            <h2 className="text-[24px] font-bold text-[#111827]">
              Lead Sources
            </h2>

            <p className="text-sm text-gray-500 mt-1">
              Manage all lead sources and channels
            </p>
          </div>

        </div>

        <div className="flex items-center gap-3">
          
          <button className="h-11 px-5 rounded-2xl border border-[#dcddea] text-[#5b5bd6] font-medium hover:bg-[#f5f5ff] transition">
            View All
          </button>

          <button className="w-11 h-11 rounded-2xl border border-[#ececf2] flex items-center justify-center hover:bg-gray-50 transition">
            <MoreVertical
              size={18}
              className="text-gray-500"
            />
          </button>

        </div>

      </div>

      {/* BUTTON */}
      <button className="mt-6 h-11 px-5 rounded-2xl border border-[#cfd2ff] bg-[#f7f7ff] text-[#5b5bd6] font-medium flex items-center gap-2 hover:bg-[#efefff] transition">
        <Plus size={18} />
        Add New
      </button>

      {/* TABLE */}
      <div className="mt-7 overflow-hidden rounded-2xl border border-[#ececf2]">
        
        <table className="w-full">
          
          <thead className="bg-[#fafafa]">
            <tr className="text-left">
              <th className="px-6 py-4 text-xs text-gray-500 font-semibold">
                SOURCE NAME
              </th>

              <th className="px-6 py-4 text-xs text-gray-500 font-semibold">
                TYPE
              </th>

              <th className="px-6 py-4 text-xs text-gray-500 font-semibold">
                STATUS
              </th>

              <th className="px-6 py-4 text-xs text-gray-500 font-semibold">
                LEADS COUNT
              </th>
            </tr>
          </thead>

          <tbody>
            {data.map((item, index) => (
              <tr
                key={index}
                className="border-t border-[#f1f1f5] hover:bg-[#fafafa] transition"
              >
                <td className="px-6 py-5 text-sm font-medium text-gray-800">
                  {item.source}
                </td>

                <td className="px-6 py-5 text-sm text-gray-600">
                  {item.type}
                </td>

                <td className="px-6 py-5">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-600">
                    Active
                  </span>
                </td>

                <td className="px-6 py-5 text-sm text-gray-700">
                  {item.leads}
                </td>
              </tr>
            ))}
          </tbody>

        </table>

      </div>

      {/* FOOTER */}
      <div className="flex items-center justify-between mt-5">
        
        <p className="text-sm text-gray-500">
          Showing 5 of 15 sources
        </p>

        <button className="text-[#5b5bd6] font-medium text-sm hover:underline">
          View All Sources →
        </button>

      </div>
    </motion.div>
  );
}