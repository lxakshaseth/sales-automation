"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

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

          {/* TOPBAR */}
          <TopBar
            title="Integrations"
            description="Connect and manage third-party platforms, communication channels and business tools."
          />

          {/* SEARCH BAR */}
          <div className="mt-6 bg-white border border-[#e5e7eb] rounded-2xl p-4 flex items-center justify-between shadow-sm mb-8">

            <div className="relative w-full max-w-[700px]">

              <input
                type="text"
                placeholder="Search integrations..."
                className="w-full h-12 px-4 rounded-xl border border-[#e5e7eb] outline-none text-sm"
              />

            </div>

            <button className="ml-5 h-12 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center gap-2">
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