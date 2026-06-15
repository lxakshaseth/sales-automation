"use client";

import { motion } from "framer-motion";
import {
  Workflow,
  Plus,
  MoreVertical,
} from "lucide-react";

const workflows = [
  {
    workflow: "New Lead Created",
    trigger: "Lead Added",
    action: "Assign Sales Rep",
    status: "Active",
  },
  {
    workflow: "Deal Won",
    trigger: "Pipeline Updated",
    action: "Send Invoice",
    status: "Active",
  },
  {
    workflow: "No Response 3 Days",
    trigger: "Lead Idle",
    action: "Send Reminder",
    status: "Active",
  },
  {
    workflow: "Lead Lost",
    trigger: "Status Changed",
    action: "Archive Lead",
    status: "Active",
  },
];

export default function WorkflowBuilder() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white border border-[#e8edf4] rounded-[22px] p-5 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#f5edff] flex items-center justify-center">
            <Workflow
              size={22}
              className="text-[#9333ea]"
            />
          </div>

          <div>
            <h2 className="text-[20px] font-bold text-[#111827]">
              Workflow Builder
            </h2>

            <p className="text-[13px] text-[#64748b] mt-1">
              Manage workflow automations
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="h-10 px-5 rounded-xl border border-[#d8b4fe] text-[#8b5cf6] text-sm font-medium flex items-center gap-2">
            <Plus size={15} />
            Create Workflow
          </button>

          <button className="h-10 px-4 rounded-xl border border-[#e5e7eb] text-[#8b5cf6] text-sm font-medium">
            View All
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
                Workflow
              </th>

              <th className="text-left px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Trigger
              </th>

              <th className="text-left px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Action
              </th>

              <th className="text-left px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Status
              </th>
            </tr>
          </thead>

          <tbody>
            {workflows.map((item, index) => (
              <tr
                key={index}
                className="border-b border-[#edf2f7] last:border-b-0"
              >
                <td className="px-5 h-[46px] text-[14px] text-[#111827]">
                  {item.workflow}
                </td>

                <td className="px-5 h-[46px] text-[14px] text-[#64748b]">
                  {item.trigger}
                </td>

                <td className="px-5 h-[46px] text-[14px] text-[#64748b]">
                  {item.action}
                </td>

                <td className="px-5 h-[46px]">
                  <span className="px-3 py-1 rounded-full text-[12px] font-medium bg-green-100 text-green-700">
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4">
        <p className="text-[13px] text-[#64748b]">
          Showing 4 workflows
        </p>

        <button className="text-[#8b5cf6] text-sm font-medium">
          View All Workflows →
        </button>
      </div>
    </motion.div>
  );
}