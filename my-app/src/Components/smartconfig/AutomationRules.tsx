"use client";

import { motion } from "framer-motion";
import {
  Settings,
  Plus,
  MoreVertical,
} from "lucide-react";

const rules = [
  {
    name: "Auto Lead Assignment",
    module: "Leads",
    status: "Active",
    updated: "Today",
  },
  {
    name: "Follow-up Reminder",
    module: "Pipeline",
    status: "Active",
    updated: "2 hrs ago",
  },
  {
    name: "Lead Scoring",
    module: "AI",
    status: "Active",
    updated: "Yesterday",
  },
  {
    name: "Auto Email Trigger",
    module: "Campaigns",
    status: "Disabled",
    updated: "3 days ago",
  },
];

export default function AutomationRules() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white border border-[#e8edf4] rounded-[22px] p-6 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-2xl bg-[#eef4ff] flex items-center justify-center">
            <Settings
              size={24}
              className="text-[#2563eb]"
            />
          </div>

          <div>
            <h2 className="text-[28px] font-bold text-[#111827]">
              Automation Rules
            </h2>

            <p className="text-[14px] text-[#64748b] mt-1">
              Manage automated business rules
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="h-11 px-5 rounded-xl border border-[#d8b4fe] text-[#8b5cf6] font-medium text-sm flex items-center gap-2">
            <Plus size={16} />
            Add Rule
          </button>

          <button className="h-11 px-5 rounded-xl border border-[#e5e7eb] text-[#8b5cf6] font-medium text-sm">
            View All
          </button>

          <button className="w-11 h-11 rounded-xl border border-[#e5e7eb] flex items-center justify-center">
            <MoreVertical
              size={18}
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
              <th className="text-left px-6 h-14 text-[12px] font-semibold text-[#64748b] uppercase">
                Rule Name
              </th>

              <th className="text-left px-6 h-14 text-[12px] font-semibold text-[#64748b] uppercase">
                Module
              </th>

              <th className="text-left px-6 h-14 text-[12px] font-semibold text-[#64748b] uppercase">
                Status
              </th>

              <th className="text-left px-6 h-14 text-[12px] font-semibold text-[#64748b] uppercase">
                Last Updated
              </th>

              <th className="text-center px-6 h-14 text-[12px] font-semibold text-[#64748b] uppercase">
                Actions
              </th>
            </tr>
          </thead>

          <tbody>
            {rules.map((rule, index) => (
              <tr
                key={index}
                className="border-b border-[#edf2f7] hover:bg-[#fafcff] transition"
              >
                <td className="px-6 h-[54px] text-[14px] font-medium text-[#111827]">
                  {rule.name}
                </td>

                <td className="px-6 h-[54px] text-[14px] text-[#475569]">
                  {rule.module}
                </td>

                <td className="px-6 h-[54px]">
                  {rule.status === "Active" ? (
                    <span className="px-3 py-1 rounded-full text-[12px] font-medium bg-green-100 text-green-700">
                      Active
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-[12px] font-medium bg-red-100 text-red-600">
                      Disabled
                    </span>
                  )}
                </td>

                <td className="px-6 h-[54px] text-[14px] text-[#64748b]">
                  {rule.updated}
                </td>

                <td className="px-6 h-[54px] text-center">
                  <MoreVertical
                    size={16}
                    className="mx-auto text-gray-500 cursor-pointer"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-5">
        <p className="text-[14px] text-[#64748b]">
          Showing 4 of 12 rules
        </p>

        <button className="text-[#8b5cf6] font-medium text-sm">
          View All Rules →
        </button>
      </div>
    </motion.div>
  );
}