"use client";

import { motion } from "framer-motion";

import {
  Building2,
  Plus,
  MoreVertical,
} from "lucide-react";

const industries = [
  {
    name: "Information Technology",
    companies: 45,
  },
  {
    name: "Healthcare",
    companies: 32,
  },
  {
    name: "Education",
    companies: 28,
  },
  {
    name: "Manufacturing",
    companies: 26,
  },
  {
    name: "Real Estate",
    companies: 18,
  },
];

export default function Industries() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-[#ececf2] rounded-3xl p-7 shadow-sm"
    >
      {/* TOP */}
      <div className="flex items-start justify-between">
        
        {/* LEFT */}
        <div className="flex items-start gap-4">
          
          <div className="w-14 h-14 rounded-2xl bg-violet-100 flex items-center justify-center">
            <Building2
              size={24}
              className="text-violet-600"
            />
          </div>

          <div>
            <h2 className="text-[24px] font-bold text-[#111827]">
              Industries
            </h2>

            <p className="text-sm text-gray-500 mt-1">
              Manage industries and business categories
            </p>
          </div>

        </div>

        {/* RIGHT */}
        <div className="flex items-center gap-3">
          
          <button className="h-11 px-5 rounded-2xl border border-[#e7e7ee] text-[#111827] font-medium hover:bg-[#f8f8fb] transition">
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

      {/* ADD BUTTON */}
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
                INDUSTRY NAME
              </th>

              <th className="px-6 py-4 text-xs text-gray-500 font-semibold">
                STATUS
              </th>

              <th className="px-6 py-4 text-xs text-gray-500 font-semibold">
                COMPANIES COUNT
              </th>

            </tr>
          </thead>

          <tbody>
            {industries.map((item, index) => (
              <tr
                key={index}
                className="border-t border-[#f1f1f5] hover:bg-[#fafafa] transition"
              >
                
                <td className="px-6 py-5 text-sm font-medium text-gray-800">
                  {item.name}
                </td>

                <td className="px-6 py-5">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-600">
                    Active
                  </span>
                </td>

                <td className="px-6 py-5 text-sm text-gray-700">
                  {item.companies}
                </td>

              </tr>
            ))}
          </tbody>

        </table>

      </div>

      {/* FOOTER */}
      <div className="flex items-center justify-between mt-5">
        
        <p className="text-sm text-gray-500">
          Showing 5 of 12 industries
        </p>

        <button className="text-[#5b5bd6] font-medium text-sm hover:underline">
          View All Industries →
        </button>

      </div>
    </motion.div>
  );
}