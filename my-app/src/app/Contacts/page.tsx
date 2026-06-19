"use client";

import { useState } from "react";
import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

import Contactlist from "@/Components/contacts/Contactlist";

export default function ContactsPage() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">
      {/* SIDEBAR */}
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
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
            title="Contacts Directory"
            description="Manage your clients, leads, and team members."
          />

          {/* CONTACTS GRID */}
          <div className="mt-6">
            <Contactlist />
          </div>

        </div>
      </main>
    </div>
  );
}