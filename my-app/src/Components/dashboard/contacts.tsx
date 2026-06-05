"use client";

import { Clock } from "lucide-react";
import { motion } from "framer-motion";

const contacts = [
  {
    initials: "RS",
    name: "Rahul Sharma",
    company: "Tech Solutions",
    time: "2 mins ago",
    status: "Hot",
  },
  {
    initials: "PP",
    name: "Priya Patel",
    company: "Global Innovators",
    time: "1 hour ago",
    status: "Warm",
  },
  {
    initials: "AK",
    name: "Amit Kumar",
    company: "NexaGen Systems",
    time: "3 hours ago",
    status: "Cold",
  },
  {
    initials: "SG",
    name: "Sneha Gupta",
    company: "Alpha Corp",
    time: "5 hours ago",
    status: "Hot",
  },
  {
    initials: "VS",
    name: "Vikram Singh",
    company: "Pioneer Tech",
    time: "1 day ago",
    status: "Warm",
  },
];

const getBadge = (status: string) => {
  switch (status) {
    case "Hot":
      return "bg-[#fee2e2] text-[#ef4444]";
    case "Warm":
      return "bg-[#ffedd5] text-[#f97316]";
    case "Cold":
      return "bg-[#dbeafe] text-[#3b82f6]";
    default:
      return "bg-gray-100 text-gray-500";
  }
};

export default function Contacts() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 25 }}
      animate={{ opacity: 1, x: 0 }}
      whileHover={{ y: -2 }}
      className="bg-white border border-[#e5e7eb] rounded-[24px] shadow-sm overflow-hidden h-full"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-[#eef2f7] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <svg
            width="16"
            height="16"
            fill="none"
            viewBox="0 0 24 24"
            stroke="#8b5cf6"
            strokeWidth="2"
          >
            <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="10" cy="7" r="4" />
            <path d="M20 8v6M23 11h-6" />
          </svg>

          <h3 className="text-[18px] font-semibold text-[#111827]">
            Contacts
          </h3>
        </div>

        <button className="text-[13px] font-medium text-[#8b5cf6] hover:text-[#7c3aed]">
          View All
        </button>
      </div>

      {/* Contact List */}
      <div className="p-4">
        <div className="space-y-5">
          {contacts.map((contact, index) => (
            <div
              key={index}
              className="flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-[#f1f5f9] flex items-center justify-center text-[12px] font-semibold text-[#64748b]">
                  {contact.initials}
                </div>

                {/* Info */}
                <div>
                  <h4 className="text-[14px] font-semibold text-[#111827]">
                    {contact.name}
                  </h4>

                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[12px] text-[#64748b]">
                      {contact.company}
                    </span>

                    <span className="text-[#cbd5e1]">•</span>

                    <Clock
                      size={10}
                      className="text-[#94a3b8]"
                    />

                    <span className="text-[12px] text-[#94a3b8]">
                      {contact.time}
                    </span>
                  </div>
                </div>
              </div>

              {/* Status Badge */}
              <span
                className={`px-3 py-1 rounded-full text-[11px] font-medium ${getBadge(
                  contact.status
                )}`}
              >
                {contact.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}