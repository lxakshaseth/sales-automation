"use client";

import { motion } from "framer-motion";
import {
  Search,
  Filter,
  ChevronDown,
  MoreHorizontal,
  Plus,
} from "lucide-react";
import { useState } from "react";

export default function HeaderSection() {
  const [showFilter, setShowFilter] = useState(false);
  const [showPipeline, setShowPipeline] = useState(false);
  const [showMore, setShowMore] = useState(false);

  const [search, setSearch] = useState("");

  return (
    <motion.div
      initial={{ opacity: 0, y: -15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex items-start justify-between flex-wrap gap-5 mb-8 relative"
    >
      {/* LEFT */}
      <div>
        <h1 className="text-[38px] font-bold text-[#111827]">
          Lead & Sales Pipeline
        </h1>

        <p className="text-[15px] text-[#6b7280] mt-2">
          Track leads and deals across pipeline stages and close more deals.
        </p>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-3 flex-wrap relative">
        {/* SEARCH */}
        <div className="flex items-center gap-3 px-4 h-[50px] rounded-xl bg-white border border-[#e5e7eb] shadow-sm">
          <Search size={16} className="text-gray-400" />

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search contacts, companies, deals..."
            className="bg-transparent outline-none text-sm text-gray-700 placeholder:text-gray-400 w-[240px]"
          />

          <span className="text-xs text-gray-500 bg-[#f3f4f6] px-2 py-1 rounded-md">
            Ctrl + K
          </span>
        </div>

        {/* FILTER */}
        <div className="relative">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => setShowFilter(!showFilter)}
            className="flex items-center gap-2 px-5 h-[50px] rounded-xl bg-white border border-[#e5e7eb] text-[#374151] font-medium shadow-sm"
          >
            <Filter size={16} />
            Filter
          </motion.button>

          {showFilter && (
            <div className="absolute top-14 left-0 w-52 bg-white border border-[#e5e7eb] rounded-xl p-2 z-50 shadow-lg">
              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Today
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                This Week
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                This Month
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Won Deals
              </div>
            </div>
          )}
        </div>

        {/* PIPELINE */}
        <div className="relative">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => setShowPipeline(!showPipeline)}
            className="flex items-center gap-2 px-5 h-[50px] rounded-xl bg-white border border-[#e5e7eb] text-[#374151] font-medium shadow-sm"
          >
            Sales Pipeline
            <ChevronDown size={16} />
          </motion.button>

          {showPipeline && (
            <div className="absolute top-14 left-0 w-56 bg-white border border-[#e5e7eb] rounded-xl p-2 z-50 shadow-lg">
              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                New Leads
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Contacted
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Qualified
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Proposal
              </div>
            </div>
          )}
        </div>

        {/* MORE */}
        <div className="relative">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => setShowMore(!showMore)}
            className="flex items-center gap-2 px-5 h-[50px] rounded-xl bg-white border border-[#e5e7eb] text-[#374151] font-medium shadow-sm"
          >
            <MoreHorizontal size={16} />
            More
          </motion.button>

          {showMore && (
            <div className="absolute top-14 right-0 w-52 bg-white border border-[#e5e7eb] rounded-xl p-2 z-50 shadow-lg">
              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Export Report
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Analytics
              </div>

              <div className="text-sm text-gray-700 hover:bg-gray-100 p-2 rounded-lg cursor-pointer">
                Team Members
              </div>

              <div className="text-sm text-red-500 hover:bg-red-50 p-2 rounded-lg cursor-pointer">
                Delete Pipeline
              </div>
            </div>
          )}
        </div>

        {/* ADD LEAD */}
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 px-6 h-[50px] rounded-xl text-white font-semibold shadow-md"
          style={{
            background:
              "linear-gradient(135deg,#7c3aed 0%, #9333ea 100%)",
          }}
        >
          <Plus size={18} />
          Add Lead
        </motion.button>
      </div>
    </motion.div>
  );
}