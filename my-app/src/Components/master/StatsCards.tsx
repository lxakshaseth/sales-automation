"use client";

import { motion } from "framer-motion";
import {
  Database,
  CheckCircle,
  Grid3X3,
  Clock3,
} from "lucide-react";

const stats = [
  {
    title: "Total Masters",
    value: "12",
    icon: Database,
    bg: "bg-violet-100",
    color: "text-violet-600",
  },
  {
    title: "Active Items",
    value: "256",
    icon: CheckCircle,
    bg: "bg-green-100",
    color: "text-green-600",
  },
  {
    title: "Categories",
    value: "8",
    icon: Grid3X3,
    bg: "bg-yellow-100",
    color: "text-yellow-600",
  },
  {
    title: "Last Updated",
    value: "2 mins ago",
    icon: Clock3,
    bg: "bg-blue-100",
    color: "text-blue-600",
  },
];

export default function StatsCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
      {stats.map((item, index) => {
        const Icon = item.icon;

        return (
          <motion.div
            key={index}
            whileHover={{
              y: -4,
              scale: 1.02,
            }}
            transition={{ duration: 0.2 }}
            className="bg-white border border-[#e8e8ef] rounded-3xl p-4 h-[95px] shadow-sm hover:shadow-md"
          >
            <div className="flex items-center justify-between h-full">
              <div>
                <p className="text-xs text-gray-500 mb-2">
                  {item.title}
                </p>

                <h3 className="text-2xl font-bold text-[#111827]">
                  {item.value}
                </h3>
              </div>

              <div
                className={`w-12 h-12 rounded-2xl flex items-center justify-center ${item.bg}`}
              >
                <Icon
                  size={22}
                  className={item.color}
                />
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}