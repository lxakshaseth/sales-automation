"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/top";

import TemplatesTable from "@/Components/templates/TemplatesTable";

export default function TemplatesPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />

      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-[90px]" : "ml-[270px]"
        }`}
      >
        <div className="p-6 lg:p-8">

          <TopBar
            title="Template Management"
            description="Create, manage, and organize reusable email templates for campaigns and automation."
          />

          <div className="mt-6">
            <TemplatesTable />
          </div>

        </div>
      </main>
    </div>
  );
}