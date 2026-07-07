"use client";

import { useSidebar } from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";
import TemplatesTable from "@/Components/templates/TemplatesTable";

export default function TemplatesPage() {
  const { isCollapsed } = useSidebar();

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "md:ml-20" : "md:ml-64"
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
