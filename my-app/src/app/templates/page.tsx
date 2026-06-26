"use client";

import { useSidebar } from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

import HeaderSection from "@/Components/templates/HeaderSection";
import TemplatesTable from "@/Components/templates/TemplatesTable";

export default function TemplatesPage() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">
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