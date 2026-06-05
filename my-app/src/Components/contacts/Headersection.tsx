"use client";

import { motion } from "framer-motion";
import {
  Bell,
  Maximize2,
  Search,
  Plus,
} from "lucide-react";

export default function ContactsHeader() {
  return (
    <div>

      {/* TOP HEADER */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <div className="flex items-start justify-between">

          <div>
            <h1 className="text-[40px] font-bold text-[#111827]">
              Contacts Directory
            </h1>

            <p className="mt-2 text-[15px] text-[#64748b]">
              Manage your clients, leads, and team members.
            </p>
          </div>

          <div className="flex items-center gap-5">

            <div className="relative">
              <Bell
                size={24}
                className="text-[#64748b]"
              />

              <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-semibold">
                6
              </span>
            </div>

            <Maximize2
              size={18}
              className="text-[#64748b]"
            />

            <div className="w-10 h-10 rounded-full bg-[#3b82f6] flex items-center justify-center text-white font-semibold">
              N
            </div>

          </div>

        </div>
      </motion.div>

      {/* SEARCH BAR */}
      <div className="bg-white border border-[#e5e7eb] rounded-2xl p-4 flex items-center justify-between shadow-sm">

        <div className="relative w-full max-w-[600px]">

          <Search
            size={20}
            className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a3b8]"
          />

          <input
            type="text"
            placeholder="Search contacts..."
            className="w-full h-12 pl-12 pr-4 rounded-xl border border-[#e5e7eb] outline-none text-sm"
          />

        </div>

        <button className="ml-5 h-12 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center gap-2">
          <Plus size={18} />
          Add Contact
        </button>

      </div>
    </div>
  );
}