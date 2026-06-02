"use client";

import {
  UserCheck,
  Lock,
  UserPlus,
  ShieldCheck,
} from "lucide-react";

const activities = [
  {
    icon: UserCheck,
    iconBg: "bg-green-100",
    iconColor: "text-green-500",
    title: "Rahul Sharma logged in",
    time: "2 minutes ago",
  },
  {
    icon: Lock,
    iconBg: "bg-orange-100",
    iconColor: "text-orange-500",
    title: "Priya Singh changed password",
    time: "1 hour ago",
  },
  {
    icon: UserPlus,
    iconBg: "bg-blue-100",
    iconColor: "text-blue-500",
    title: "New user Amit Verma added",
    time: "3 hours ago",
  },
  {
    icon: ShieldCheck,
    iconBg: "bg-purple-100",
    iconColor: "text-purple-500",
    title: "Snehal Jadhav updated role permissions",
    time: "5 hours ago",
  },
];

export default function RecentActivity() {
  return (
    <div className="bg-white border border-[#e7ebf3] rounded-3xl shadow-sm p-8">

      {/* HEADER */}
      <div className="mb-8">
        <h2 className="text-[26px] font-bold text-[#111827]">
          Recent Activity
        </h2>

        <p className="text-[15px] text-[#64748b] mt-1">
          Latest user activities in the system
        </p>
      </div>

      {/* ACTIVITIES */}
      <div>

        {activities.map((item, index) => {
          const Icon = item.icon;

          return (
            <div key={index}>
              <div className="flex items-center justify-between py-1">

                <div className="flex items-center gap-5">

                  <div
                    className={`w-14 h-14 rounded-full flex items-center justify-center ${item.iconBg}`}
                  >
                    <Icon
                      size={24}
                      className={item.iconColor}
                    />
                  </div>

                  <h3 className="text-[18px] font-medium text-[#111827]">
                    {item.title}
                  </h3>
                </div>

                <p className="text-[16px] text-[#64748b]">
                  {item.time}
                </p>
              </div>

              {index !== activities.length - 1 && (
                <div className="border-b border-[#eef2f7]" />
              )}
            </div>
          );
        })}

      </div>

      {/* FOOTER LINK */}
      <div className="mt-8">
        <button className="text-[18px] font-semibold text-violet-600 hover:text-violet-700 transition">
          View all activities
        </button>
      </div>

    </div>
  );
}