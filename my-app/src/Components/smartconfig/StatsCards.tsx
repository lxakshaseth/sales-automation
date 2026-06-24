"use client";

import { motion } from "framer-motion";
import {
  Settings,
  Bot,
  Workflow,
  BellRing,
} from "lucide-react";

const cards = [
  {
    title: "Automation Rules",
    value: "48",
    subtitle: "Active Rules",
    icon: Settings,
    bg: "bg-[#eaf2ff]",
    color: "text-[#2563eb]",
  },
  {
    title: "AI Agents",
    value: "12",
    subtitle: "Running Agents",
    icon: Bot,
    bg: "bg-[#e8f8ee]",
    color: "text-[#16a34a]",
  },
  {
    title: "Workflows",
    value: "36",
    subtitle: "Configured Flows",
    icon: Workflow,
    bg: "bg-[#f5edff]",
    color: "text-[#9333ea]",
  },
  {
    title: "Notifications",
    value: "124",
    subtitle: "Triggered Today",
    icon: BellRing,
    bg: "bg-[#fff2e8]",
    color: "text-[#f97316]",
  },
];

export function StatsCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
      {cards.map((card, index) => {
        const Icon = card.icon;

        return (
          <motion.div
            key={index}
            whileHover={{ y: -2 }}
            transition={{ duration: 0.2 }}
            className="bg-white border border-[#edf0f5] rounded-[18px] px-5 py-5 shadow-sm"
          >
            <div className="flex items-center gap-4">
              
              {/* Icon */}
              <div
                className={`w-[58px] h-[58px] rounded-2xl flex items-center justify-center ${card.bg}`}
              >
                <Icon
                  size={28}
                  strokeWidth={2}
                  className={card.color}
                />
              </div>

              {/* Content */}
              <div>
                <p className="text-[12px] font-medium text-[#64748b]">
                  {card.title}
                </p>

                <h2 className="text-[40px] leading-none font-bold text-[#111827] mt-1">
                  {card.value}
                </h2>

                <p className="text-[13px] text-[#94a3b8] mt-1">
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