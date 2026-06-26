"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

import StatsCards from "@/Components/master/StatsCards";
import LeadSources from "@/Components/master/LeadSources";
import LeadStatus from "@/Components/master/LeadStatus";
import Industries from "@/Components/master/Industries";

export default function MasterPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">

      {/* SIDEBAR */}
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() =>
          setIsCollapsed(!isCollapsed)
        }
      />

      {/* RIGHT CONTENT */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-22.5" : "ml-67.5"
        }`}
      >
        <div className="p-8">

          {/* TOPBAR */}
          <TopBar
            title="Master"
            description="Manage all master data and lookups"
          />

          {/* STATS */}
          <div className="mt-6">
            <StatsCards />
          </div>

          {/* LEAD SOURCES */}
          <div className="mt-8">
            <LeadSources />
          </div>

          {/* LEAD STATUS */}
          <div className="mt-8">
            <LeadStatus />
          </div>

          {/* INDUSTRIES */}
          <div className="mt-8 pb-10">
            <Industries />
          </div>

        </div>
      </main>
    </div>
  );
}