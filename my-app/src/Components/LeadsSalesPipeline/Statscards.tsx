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
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400",
    change: "+12%",
    positive: true,
  },
  {
    label: "Total Value",
    value: "₹48,75,000",
    icon: DollarSign,
    iconBg: "bg-emerald-500/20",
    iconColor: "text-emerald-400",
    change: "+18%",
    positive: true,
  },
  {
    label: "Open Deals",
    value: "97",
    icon: Package,
    iconBg: "bg-orange-500/20",
    iconColor: "text-orange-400",
    change: "+8%",
    positive: true,
  },
  {
    label: "Won Deals",
    value: "21",
    icon: CheckCircle,
    iconBg: "bg-green-500/20",
    iconColor: "text-green-400",
    change: "+25%",
    positive: true,
  },
  {
    label: "Lost Deals",
    value: "10",
    icon: XCircle,
    iconBg: "bg-red-500/20",
    iconColor: "text-red-400",
    change: "-5%",
    positive: false,
  },
  {
    label: "Win Rate",
    value: "21.65%",
    icon: TrendingUp,
    iconBg: "bg-violet-500/20",
    iconColor: "text-violet-400",
    change: "+10%",
    positive: true,
  },
];

export default function StatsCards() {
  return (
    <div className="grid grid-cols-2 xl:grid-cols-6 gap-4 mb-8">
      {stats.map((item, index) => {
        const Icon = item.icon;

        return (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 25 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            whileHover={{
              y: -5,
              boxShadow: "0 0 25px rgba(124,58,237,0.18)",
            }}
            className="bg-[#141419] border border-[#24242b] rounded-3xl p-5"
          >
            <div
              className={`w-14 h-14 rounded-2xl flex items-center justify-center mb-5 ${item.iconBg}`}
            >
              <Icon className={`w-7 h-7 ${item.iconColor}`} />
            </div>

            <h4 className="text-sm text-gray-300 font-medium">
              {item.label}
            </h4>

            <h2 className="text-3xl font-bold text-white mt-2">
              {item.value}
            </h2>

            <div className="flex items-center gap-1 mt-3">
              <span
                className={`text-sm font-semibold ${
                  item.positive ? "text-green-400" : "text-red-400"
                }`}
              >
                {item.positive ? "↑" : "↓"} {item.change}
              </span>

              <span className="text-sm text-gray-400">
                vs last month
              </span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}