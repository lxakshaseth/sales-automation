import { motion } from "framer-motion";

import {
  UserPlus,
  MessageSquare,
  ContactRound,
  Rocket,
} from "lucide-react";

const cards = [
  {
    title: "Our Leads",
    value: "1,240",
    subtitle: "vs last month",
    change: "+12.5%",
    icon: UserPlus,
    iconBg: "bg-[#eaf2ff]",
    iconColor: "text-[#2563eb]",
  },
  {
    title: "Live Chat Feed",
    value: "342",
    subtitle: "vs last month",
    change: "+5.2%",
    icon: MessageSquare,
    iconBg: "bg-[#dcfce7]",
    iconColor: "text-[#16a34a]",
  },
  {
    title: "Contacts",
    value: "8,549",
    subtitle: "vs last month",
    change: "+2.4%",
    icon: ContactRound,
    iconBg: "bg-[#f3e8ff]",
    iconColor: "text-[#9333ea]",
  },
  {
    title: "Campaigns",
    value: "12",
    subtitle: "Active Campaigns",
    change: "+2 Active",
    icon: Rocket,
    iconBg: "bg-[#ffedd5]",
    iconColor: "text-[#f97316]",
  },
];


export function StatsCards() {
  
  return (
    <div>
     

      {/* STATS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">

        {cards.map((card, index) => {
          const Icon = card.icon;

          return (
            <motion.div
              key={index}
              whileHover={{ y: -3 }}
              transition={{ duration: 0.2 }}
              className="bg-white border border-[#e5e7eb] rounded-[20px] px-6 py-6 shadow-sm"
            >
              <div className="flex items-start justify-between">

                {/* LEFT SIDE */}
                <div className="flex items-start gap-4">

                  <div
                    className={`w-[62px] h-[62px] rounded-[18px] flex items-center justify-center ${card.iconBg}`}
                  >
                    <Icon
                      size={28}
                      className={card.iconColor}
                      strokeWidth={2}
                    />
                  </div>

                  <div>
                    <p className="text-[13px] font-medium text-[#64748b]">
                      {card.title}
                    </p>

                    <h2 className="text-[22px] font-bold text-[#111827] mt-1">
                      {card.value}
                    </h2>

                    <p className="text-[12px] text-[#94a3b8] mt-1">
                      {card.subtitle}
                    </p>
                  </div>

                </div>

                {/* RIGHT BADGE */}
                <span className="px-3 py-1 rounded-full bg-[#dcfce7] text-[#16a34a] text-[12px] font-semibold whitespace-nowrap">
                  {card.change}
                </span>

              </div>
            </motion.div>
          );
        })}

      </div>
    </div>
  );
}