"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";

import {
  Bell,
  Maximize2,
  Search,
  Plus,
} from "lucide-react";

import IntegrationCards from "@/Components/integration/IntegrationCards";

export default function IntegrationPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">

      {/* SIDEBAR */}
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() =>
          setIsCollapsed(!isCollapsed)
        }
      />

      {/* MAIN CONTENT */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-[90px]" : "ml-[270px]"
        }`}
      >
        <div className="p-6 lg:p-8">

          {/* HEADER */}
          <div className="flex items-start justify-between mb-8">

            <div>
              <h1 className="text-[42px] font-bold text-[#111827] leading-none">
                Integrations
              </h1>

              <p className="mt-3 text-[15px] text-[#64748b]">
                Connect and manage third-party platforms,
                communication channels and business tools.
              </p>
            </div>

            <div className="flex items-center gap-5">

              <div className="relative">
                <Bell
                  size={22}
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

          {/* SEARCH BAR */}
          <div className="bg-white border border-[#e5e7eb] rounded-2xl p-4 flex items-center justify-between shadow-sm mb-8">

            <div className="relative w-full max-w-[700px]">

              <Search
                size={20}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a3b8]"
              />

              <input
                type="text"
                placeholder="Search integrations..."
                className="w-full h-12 pl-12 pr-4 rounded-xl border border-[#e5e7eb] outline-none text-sm"
              />

            </div>

            <button className="ml-5 h-12 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center gap-2">
              <Plus size={18} />
              Add Integration
            </button>

          </div>

          {/* INTEGRATION CARDS */}
          <IntegrationCards />

        </div>
      </main>
    </div>
  );
}