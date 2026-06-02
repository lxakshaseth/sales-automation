"use client";

import { motion } from "framer-motion";
import {
  Users,
  UserCheck,
  ShieldCheck,
  UserPlus,
} from "lucide-react";

const cards = [
  {
    title: "Total Users",
    value: "156",
    subtitle: "All registered users",
    icon: Users,
    bg: "bg-blue-100",
    color: "text-blue-600",
  },
  {
    title: "Active Users",
    value: "142",
    subtitle: "Currently active users",
    icon: UserCheck,
    bg: "bg-green-100",
    color: "text-green-600",
  },
  {
    title: "Admins",
    value: "12",
    subtitle: "Users with admin role",
    icon: ShieldCheck,
    bg: "bg-purple-100",
    color: "text-purple-600",
  },
  {
    title: "New Users This Month",
    value: "24",
    subtitle: "Users added this month",
    icon: UserPlus,
    bg: "bg-orange-100",
    color: "text-orange-600",
  },
];

export default function StatsCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {cards.map((card, index) => {
        const Icon = card.icon;

        return (
          <motion.div
            key={index}
            whileHover={{
              y: -4,
              scale: 1.02,
            }}
            transition={{ duration: 0.2 }}
            className="bg-white border border-[#e5e7eb] rounded-3xl p-5 shadow-sm hover:shadow-md"
          >
            <div className="flex items-center gap-4">
              
              {/* ICON */}
              <div
                className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${card.bg}`}
              >
                <Icon
                  size={26}
                  className={card.color}
                />
              </div>

              {/* CONTENT */}
              <div>
                <p className="text-sm font-medium text-gray-500">
                  {card.title}
                </p>

                <h2 className="text-[38px] leading-none font-bold text-[#111827] mt-2">
                  {card.value}
                </h2>

                <p className="text-sm text-gray-400 mt-2">
                  {card.subtitle}
                </p>
              </div>

            </div>
          </motion.div>
        );
      })}
    </div>
  );
}