"use client";

import { motion } from "framer-motion";
import { useState } from "react";

import {
  UserPlus,
  MessageSquare,
  ContactRound,
  Rocket,
  Bell,
  Maximize2,
  LogOut,
  User
} from "lucide-react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";


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
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem("token")
    toast.success("Logout Succesfully")
    router.push("/sign-in")
  }
  return (
    <div>
      {/* HEADER */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-start justify-between">

          <div>
            <h1 className="text-[42px] font-bold text-[#111827] leading-none">
              Dashboard Overview
            </h1>

            <p className="mt-3 text-[16px] text-[#64748b]">
              Monitor leads, conversations, campaigns, contacts and sales
              performance.
            </p>
          </div>

          <div className="flex items-center gap-6">

            <div className="relative cursor-pointer">
              <Bell
                size={28}
                className="text-[#64748b]"
              />

              <span className="absolute -top-2 -right-2 flex items-center justify-center w-5 h-5 rounded-full bg-red-500 text-white text-[10px] font-semibold">
                6
              </span>
            </div>

            <Maximize2
              size={18}
              className="text-[#64748b] cursor-pointer"
            />

            <div className="relative">
              <div
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="w-11 h-11 rounded-full bg-[#3b82f6] flex items-center justify-center text-white font-semibold cursor-pointer"
              >
              User
              </div>

              {showProfileMenu && (
                <div className="absolute right-0 top-14 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">

                  <button
                    className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 text-left"
                  >
                    <User size={18} />
                    <span>Profile</span>
                  </button>

                  <button
                    onClick={handleLogout}
                    className="w-full px-4 py-3 flex items-center gap-3 hover:bg-red-50 text-red-600 text-left"
                  >
                    <LogOut size={18} />
                    <span>Logout</span>
                  </button>

                </div>
              )}
            </div>

          </div>

        </div>
      </motion.div>

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