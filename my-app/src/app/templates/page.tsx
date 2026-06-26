"use client";

import { useState } from "react";
import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

import TemplatesTable from "@/Components/templates/TemplatesTable";

export default function TemplatesPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />

      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-20" : "ml-64"
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