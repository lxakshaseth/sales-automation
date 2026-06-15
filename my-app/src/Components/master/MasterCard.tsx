"use client";

import { motion } from "framer-motion";
import { MoreVertical } from "lucide-react";

type MasterCardProps = {
  icon: React.ReactNode;
  iconBg: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
};

export function ActiveBadge() {
  return (
    <span className="px-3 py-1 text-xs font-medium rounded-full bg-green-100 text-green-600">
      Active
    </span>
  );
}

export default function MasterCard({
  icon,
  iconBg,
  title,
  subtitle,
  children,
}: MasterCardProps) {
  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
      className="bg-white border border-[#ececf2] rounded-3xl p-6 shadow-sm"
    >
      {/* TOP */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-4">
          <div
            className={`w-14 h-14 rounded-2xl flex items-center justify-center ${iconBg}`}
          >
            {icon}
          </div>

          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {title}
            </h2>

            <p className="text-sm text-gray-500 mt-1">
              {subtitle}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="px-5 py-2 rounded-xl border border-[#e7e7ee] text-sm font-medium hover:bg-gray-50 transition">
            View All
          </button>

          <button className="w-10 h-10 rounded-xl hover:bg-gray-100 flex items-center justify-center transition">
            <MoreVertical size={18} />
          </button>
        </div>
      </div>

      {/* CONTENT */}
      {children}
    </motion.div>
  );
}
export function Td({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <td className="py-4 text-sm text-gray-700">
      {children}
    </td>
  );
}