"use client";

import { Users } from "lucide-react";

const leads = [
  {
    initials: "RS",
    bg: "bg-[#E9D5FF]",
    text: "text-[#9333EA]",
    name: "Rahul Sharma",
    source: "Website",
    value: "₹2,50,000",
    date: "2 mins ago",
  },
  {
    initials: "PP",
    bg: "bg-[#DBEAFE]",
    text: "text-[#2563EB]",
    name: "Priya Patel",
    source: "Facebook Ads",
    value: "₹1,80,000",
    date: "1 hour ago",
  },
  {
    initials: "AK",
    bg: "bg-[#DCFCE7]",
    text: "text-[#16A34A]",
    name: "Amit Kumar",
    source: "LinkedIn",
    value: "₹3,20,000",
    date: "3 hours ago",
  },
  {
    initials: "SG",
    bg: "bg-[#FEE2E2]",
    text: "text-[#EF4444]",
    name: "Sneha Gupta",
    source: "Referral",
    value: "₹1,10,000",
    date: "5 hours ago",
  },
  {
    initials: "VS",
    bg: "bg-[#FFEDD5]",
    text: "text-[#F97316]",
    name: "Vikram Singh",
    source: "Walk-in",
    value: "₹2,80,000",
    date: "1 day ago",
  },
];

export default function RecentLeads() {
  return (
    <div className="bg-white border border-[#E5E7EB] rounded-[18px] shadow-sm overflow-hidden">

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#F1F5F9]">

        <div className="flex items-center gap-2">
          <Users
            size={14}
            className="text-[#94A3B8]"
          />

          <h3 className="text-[15px] font-semibold text-[#111827]">
            Recent Leads
          </h3>
        </div>

        <button className="text-[13px] font-medium text-[#8B5CF6] hover:text-[#7C3AED]">
          View All
        </button>

      </div>

      {/* Table Header */}
      <div className="grid grid-cols-[2.2fr_1.3fr_1.5fr_1.2fr] px-5 py-3 text-[11px] font-medium text-[#94A3B8] border-b border-[#F8FAFC]">

        <div>Name</div>
        <div>Source</div>
        <div>Potential Value</div>
        <div>Added On</div>

      </div>

      {/* Rows */}
      <div className="divide-y divide-[#F8FAFC]">

        {leads.map((lead, index) => (
          <div
            key={index}
            className="grid grid-cols-[2.2fr_1.3fr_1.5fr_1.2fr] items-center px-5 py-[11px]"
          >
            {/* Name */}
            <div className="flex items-center gap-3">

              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-semibold ${lead.bg} ${lead.text}`}
              >
                {lead.initials}
              </div>

              <span className="text-[13px] text-[#111827] font-medium">
                {lead.name}
              </span>

            </div>

            {/* Source */}
            <div className="text-[13px] text-[#475569]">
              {lead.source}
            </div>

            {/* Value */}
            <div className="text-[13px] font-medium text-[#111827]">
              {lead.value}
            </div>

            {/* Date */}
            <div className="text-[13px] text-[#64748B]">
              {lead.date}
            </div>
          </div>
        ))}

      </div>
    </div>
  );
}