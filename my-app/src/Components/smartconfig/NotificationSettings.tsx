"use client";

import { motion } from "framer-motion";
import {
  Bell,
  MoreVertical,
} from "lucide-react";

const notifications = [
  {
    type: "Lead Assignment Alerts",
    channel: "Email",
    status: "Active",
  },
  {
    type: "Deal Won Alerts",
    channel: "WhatsApp",
    status: "Active",
  },
  {
    type: "Workflow Error Alerts",
    channel: "Browser",
    status: "Active",
  },
  {
    type: "Weekly Reports",
    channel: "Email",
    status: "Disabled",
  },
  {
    type: "AI Alerts",
    channel: "Browser",
    status: "Active",
  },
];

export default function NotificationSettings() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white border border-[#e8edf4] rounded-[22px] p-5 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-start gap-3">
          
          <div className="w-12 h-12 rounded-2xl bg-[#fff4e8] flex items-center justify-center">
            <Bell
              size={22}
              className="text-[#f97316]"
            />
          </div>

          <div>
            <h2 className="text-[20px] font-bold text-[#111827]">
              Notification Settings
            </h2>

            <p className="text-[13px] text-[#64748b] mt-1">
              Manage alert preferences
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          
          <button className="h-10 px-5 rounded-xl border border-[#d8b4fe] text-[#8b5cf6] text-sm font-medium bg-white">
            Save Preferences
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
                Notification Type
              </th>

              <th className="text-left px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Channel
              </th>

              <th className="text-left px-5 h-12 text-[11px] font-semibold text-[#64748b] uppercase">
                Status
              </th>

            </tr>
          </thead>

          <tbody>
            {notifications.map((item, index) => (
              <tr
                key={index}
                className="border-b border-[#edf2f7] last:border-b-0"
              >
                <td className="px-5 h-[52px] text-[14px] font-medium text-[#111827]">
                  {item.type}
                </td>

                <td className="px-5 h-[52px] text-[14px] text-[#475569]">
                  {item.channel}
                </td>

                <td className="px-5 h-[52px]">
                  {item.status === "Active" ? (
                    <span className="px-3 py-1 rounded-full text-[12px] font-medium bg-green-100 text-green-700">
                      Active
                    </span>
                  ) : (
                    <span className="px-3 py-1 rounded-full text-[12px] font-medium bg-red-100 text-red-500">
                      Disabled
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-5">
        <p className="text-[13px] text-[#64748b]">
          Showing 5 notification settings
        </p>
      </div>
    </motion.div>
  );
}