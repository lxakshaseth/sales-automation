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
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="flex items-start justify-between flex-wrap gap-5 mb-8 relative"
    >
      
      {/* LEFT */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight">
          Lead & Sales Pipeline
        </h1>

        <p className="text-sm mt-2 text-gray-300">
          Track leads and deals across pipeline stages and close more deals.
        </p>
      </div>

      {/* RIGHT */}
      <div className="flex items-center gap-3 flex-wrap relative">

        {/* SEARCH */}
        <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-[#141419] border border-[#24242b]">

          <Search size={16} className="text-gray-400" />

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search contacts, companies, deals..."
            className="bg-transparent outline-none text-sm text-white placeholder:text-gray-500 w-[220px]"
          />

          <span className="text-xs text-gray-500 bg-[#1e1e25] px-2 py-1 rounded-lg">
            Ctrl + K
          </span>
        </div>

        {/* FILTER */}
        <div className="relative">

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowFilter(!showFilter)}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-[#141419] border border-[#24242b] text-white font-medium"
          >
            <Filter size={16} />
            Filter
          </motion.button>

          {showFilter && (
            <div className="absolute top-16 left-0 w-52 bg-[#18181f] border border-[#2a2a35] rounded-2xl p-3 z-50 shadow-2xl">
              
              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Today
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                This Week
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                This Month
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Won Deals
              </div>

            </div>
          )}
        </div>

        {/* SALES PIPELINE */}
        <div className="relative">

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowPipeline(!showPipeline)}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-[#141419] border border-[#24242b] text-white font-medium"
          >
            Sales Pipeline
            <ChevronDown size={16} />
          </motion.button>

          {showPipeline && (
            <div className="absolute top-16 left-0 w-56 bg-[#18181f] border border-[#2a2a35] rounded-2xl p-3 z-50 shadow-2xl">

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                New Leads
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Contacted
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Qualified
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Proposal
              </div>

            </div>
          )}
        </div>

        {/* MORE */}
        <div className="relative">

          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowMore(!showMore)}
            className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-[#141419] border border-[#24242b] text-white font-medium"
          >
            <MoreHorizontal size={16} />
            More
          </motion.button>

          {showMore && (
            <div className="absolute top-16 right-0 w-52 bg-[#18181f] border border-[#2a2a35] rounded-2xl p-3 z-50 shadow-2xl">

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Export Report
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Analytics
              </div>

              <div className="text-sm text-gray-300 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Team Members
              </div>

              <div className="text-sm text-red-400 hover:bg-[#24242b] p-2 rounded-xl cursor-pointer">
                Delete Pipeline
              </div>

            </div>
          )}
        </div>

        {/* ADD LEAD */}
        <motion.button
          whileHover={{
            scale: 1.04,
            boxShadow: "0 0 25px rgba(168,85,247,0.4)",
          }}
          whileTap={{ scale: 0.95 }}
          className="flex items-center gap-2 px-5 py-3 rounded-2xl font-semibold text-white"
          style={{
            background: "linear-gradient(135deg,#7c3aed,#a855f7)",
          }}
        >
          <Plus size={18} />
          Add Lead
        </motion.button>

      </div>
    </motion.div>
  );
}