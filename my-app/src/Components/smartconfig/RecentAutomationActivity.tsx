"use client";

import { motion } from "framer-motion";
import {
  Activity,
  CheckCircle2,
  Clock3,
  Brain,
  ShieldCheck,
  XCircle,
  MoreVertical,
} from "lucide-react";

const activities = [
  {
    title: "Lead Auto Assigned",
    description:
      "Lead has been automatically assigned to Neelam Chauhan",
    time: "2 min ago",
    icon: CheckCircle2,
    bg: "bg-green-100",
    color: "text-green-600",
  },
  {
    title: "Follow-up Reminder Sent",
    description:
      "Reminder email sent to 12 leads",
    time: "15 min ago",
    icon: Clock3,
    bg: "bg-yellow-100",
    color: "text-yellow-600",
  },
  {
    title: "AI Scored New Lead",
    description:
      "Lead scoring completed for 8 new leads",
    time: "1 hour ago",
    icon: Brain,
    bg: "bg-orange-100",
    color: "text-orange-500",
  },
  {
    title: "Workflow Executed Successfully",
    description:
      "New Lead Created workflow executed",
    time: "3 hours ago",
    icon: ShieldCheck,
    bg: "bg-green-100",
    color: "text-green-600",
  },
  {
    title: "Notification Failed",
    description:
      "Failed to send WhatsApp notification",
    time: "Yesterday",
    icon: XCircle,
    bg: "bg-red-100",
    color: "text-red-500",
  },
];

export default function RecentAutomationActivity() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white border border-[#e8edf4] rounded-[22px] p-5 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div className="flex items-start gap-3">
          
          <div className="w-12 h-12 rounded-2xl bg-[#eef4ff] flex items-center justify-center">
            <Activity
              size={22}
              className="text-[#3b82f6]"
            />
          </div>

          <div>
            <h2 className="text-[20px] font-bold text-[#111827]">
              Recent Automation Activity
            </h2>

            <p className="text-[13px] text-[#64748b] mt-1">
              Latest automation executions
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          
          <button className="h-10 px-5 rounded-xl border border-[#d8b4fe] text-[#8b5cf6] text-sm font-medium">
            View All Activities
          </button>

          <button className="w-10 h-10 rounded-xl border border-[#e5e7eb] flex items-center justify-center">
            <MoreVertical
              size={16}
              className="text-gray-500"
            />
          </button>

        </div>
      </div>

      {/* Activities */}
      <div className="border border-[#edf2f7] rounded-2xl overflow-hidden">
        {activities.map((item, index) => {
          const Icon = item.icon;

          return (
            <div
              key={index}
              className={`flex items-center justify-between px-5 py-4 ${
                index !== activities.length - 1
                  ? "border-b border-[#edf2f7]"
                  : ""
              }`}
            >
              <div className="flex items-center gap-4">
                
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${item.bg}`}
                >
                  <Icon
                    size={18}
                    className={item.color}
                  />
                </div>

                <div>
                  <h4 className="text-[15px] font-semibold text-[#111827]">
                    {item.title}
                  </h4>

                  <p className="text-[13px] text-[#64748b] mt-0.5">
                    {item.description}
                  </p>
                </div>
              </div>

              <p className="text-[13px] text-[#64748b] whitespace-nowrap">
                {item.time}
              </p>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex justify-end mt-5">
        <button className="text-[#8b5cf6] text-sm font-medium">
          View All Activities →
        </button>
      </div>
    </motion.div>
  );
}