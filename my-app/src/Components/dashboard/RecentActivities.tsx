"use client";

import {
  UserPlus,
  Megaphone,
  CheckCircle,
  UserCog,
  ClipboardList,
} from "lucide-react";

const activities = [
  {
    icon: UserPlus,
    title: "Lead Added",
    description: "New lead Rahul Sharma added",
    time: "2 mins ago",
    bg: "bg-[#DBEAFE]",
    color: "text-[#2563EB]",
  },
  {
    icon: Megaphone,
    title: "Campaign Created",
    description: "WhatsApp Summer Campaign created",
    time: "1 hour ago",
    bg: "bg-[#FFEDD5]",
    color: "text-[#F97316]",
  },
  {
    icon: CheckCircle,
    title: "Deal Closed",
    description: "Deal worth ₹2,40,000 closed",
    time: "3 hours ago",
    bg: "bg-[#DCFCE7]",
    color: "text-[#16A34A]",
  },
  {
    icon: UserCog,
    title: "User Updated",
    description: "Priya Patel updated profile information",
    time: "Yesterday",
    bg: "bg-[#E9D5FF]",
    color: "text-[#9333EA]",
  },
  {
    icon: ClipboardList,
    title: "Status Changed",
    description: "Lead status changed to Qualified",
    time: "Yesterday",
    bg: "bg-[#E2E8F0]",
    color: "text-[#64748B]",
  },
];

export default function RecentActivities() {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-[18px] shadow-sm h-[260px] overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#F1F5F9]">

        <div className="flex items-center gap-2">
          <ClipboardList
            size={14}
            className="text-[#94A3B8]"
          />

          <h3 className="text-[15px] font-semibold text-[#111827]">
            Recent Activities
          </h3>
        </div>

        <button className="text-[13px] font-medium text-[#8B5CF6]">
          View All
        </button>

      </div>

      {/* Activities */}
      <div className="px-5 py-4">

        {activities.map((activity, index) => {
          const Icon = activity.icon;

          return (
            <div
              key={index}
              className="flex items-start justify-between mb-4 last:mb-0"
            >
              <div className="flex gap-3">

                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center ${activity.bg}`}
                >
                  <Icon
                    size={14}
                    className={activity.color}
                  />
                </div>

                <div>
                  <h4 className="text-[13px] font-medium text-[#111827] leading-none">
                    {activity.title}
                  </h4>

                  <p className="text-[11px] text-[#94A3B8] mt-1">
                    {activity.description}
                  </p>
                </div>

              </div>

              <span className="text-[12px] text-[#64748B] whitespace-nowrap">
                {activity.time}
              </span>
            </div>
          );
        })}

      </div>
    </div>
  );
}