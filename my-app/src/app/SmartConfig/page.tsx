"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";

import {
  HeaderSection,
  StatsCards,
} from "@/Components/smartconfig/StatsCards";

import AutomationRules from "@/Components/smartconfig/AutomationRules";
import AIConfiguration from "@/Components/smartconfig/AIConfiguration";
import WorkflowBuilder from "@/Components/smartconfig/WorkflowBuilder";
import NotificationSettings from "@/Components/smartconfig/NotificationSettings";
import RecentAutomationActivity from "@/Components/smartconfig/RecentAutomationActivity";

export default function SmartConfigPage() {
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
          <HeaderSection />

          {/* STATS */}
          <div className="mt-6">
            <StatsCards />
          </div>

          {/* AUTOMATION RULES */}
          <div className="mt-6">
            <AutomationRules />
          </div>

          {/* AI + WORKFLOW */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">
            <AIConfiguration />
            <WorkflowBuilder />
          </div>

          {/* NOTIFICATION + ACTIVITY */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6 pb-8">
            <NotificationSettings />
            <RecentAutomationActivity />
          </div>

        </div>
      </main>
    </div>
  );
}