"use client";

import { motion } from "framer-motion";

import {
  Briefcase,
  DollarSign,
  Package,
  CheckCircle,
  XCircle,
  TrendingUp,
} from "lucide-react";

const stats = [
  {
    label: "Total Deals",
    value: "128",
    icon: Briefcase,
    iconBg: "bg-blue-100",
    iconColor: "text-blue-600",
    change: "+12%",
    positive: true,
  },
  {
    label: "Total Value",
    value: "₹48,75,000",
    icon: DollarSign,
    iconBg: "bg-emerald-100",
    iconColor: "text-emerald-600",
    change: "+18%",
    positive: true,
  },
  {
    label: "Open Deals",
    value: "97",
    icon: Package,
    iconBg: "bg-orange-100",
    iconColor: "text-orange-600",
    change: "+8%",
    positive: true,
  },
  {
    label: "Won Deals",
    value: "21",
    icon: CheckCircle,
    iconBg: "bg-green-100",
    iconColor: "text-green-600",
    change: "+25%",
    positive: true,
  },
  {
    label: "Lost Deals",
    value: "10",
    icon: XCircle,
    iconBg: "bg-red-100",
    iconColor: "text-red-600",
    change: "-5%",
    positive: false,
  },
  {
    label: "Win Rate",
    value: "21.65%",
    icon: TrendingUp,
    iconBg: "bg-violet-100",
    iconColor: "text-violet-600",
    change: "+10%",
    positive: true,
  },
];

export default function StatsCards() {
  return (
    <div className="grid grid-cols-2 xl:grid-cols-6 gap-5 mb-8">
      {stats.map((item, index) => {
        const Icon = item.icon;

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{
              y: -5,
              scale: 1.02,
            }}
            className="bg-white border border-[#e5e7eb] rounded-3xl p-5 shadow-sm hover:shadow-lg transition-all"
          >
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-5 ${item.iconBg}`}
            >
              <Icon
                className={`w-7 h-7 ${item.iconColor}`}
              />
            </div>

            <h4 className="text-sm text-[#64748b] font-medium">
              {item.label}
            </h4>

            <h2 className="text-3xl font-bold text-[#111827] mt-2">
              {item.value}
            </h2>

            <div className="flex items-center gap-1 mt-3">
              <span
                className={`text-sm font-semibold ${
                  item.positive
                    ? "text-green-600"
                    : "text-red-600"
                }`}
              >
                {item.positive ? "↑" : "↓"} {item.change}
              </span>

              <span className="text-sm text-[#94a3b8]">
                vs last month
              </span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}