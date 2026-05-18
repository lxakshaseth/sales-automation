"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";

const activities = [
  {
    text: "Rahul Verma moved from Contacted to Qualified",
    time: "2h ago",
    color: "bg-blue-400",
  },
  {
    text: "Proposal sent to Sneha Iyer",
    time: "4h ago",
    color: "bg-violet-400",
  },
  {
    text: "Deal won — Amit Kumar (₹50,000)",
    time: "1d ago",
    color: "bg-green-400",
  },
  {
    text: "Task scheduled for Arjun Nair",
    time: "1d ago",
    color: "bg-orange-400",
  },
  {
    text: "Harsh Agarwal moved to Negotiation",
    time: "2d ago",
    color: "bg-red-400",
  },
];

export default function RecentActivities() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-[#141419] border border-[#24242b] rounded-3xl p-4"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-white">
          Recent Activities
        </h2>

        {/* Dropdown */}
        <select className="px-4 py-2 rounded-xl bg-[#1b1b22] border border-[#2b2b35] text-sm text-white outline-none cursor-pointer">
          <option>All Activities</option>
          <option>Calls</option>
          <option>Meetings</option>
          <option>Emails</option>
          <option>Deals</option>
        </select>
      </div>

      <div className="space-y-4">
        {activities.map((item, index) => (
          <div
            key={index}
            className="
              flex items-start justify-between
              border-b border-[#24242b]
              pb-4
              transition-all duration-300
              hover:bg-[#1b1b22]
              hover:px-2
              hover:rounded-xl
            "
          >
            <div className="flex items-start gap-3">
              <div
                className={`w-2.5 h-2.5 rounded-full mt-2 ${item.color}`}
              />

              <p className="text-sm text-gray-200 leading-6">
                {item.text}
              </p>
            </div>

            <span className="text-xs text-gray-500 whitespace-nowrap">
              {item.time}
            </span>
          </div>
        ))}
      </div>

      <button className="flex items-center gap-2 text-violet-400 mt-5 text-sm font-medium hover:gap-3 transition-all duration-300">
        View All Activities
        <ArrowRight size={15} />
      </button>
    </motion.div>
  );
}