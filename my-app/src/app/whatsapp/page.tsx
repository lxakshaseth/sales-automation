"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";

import WhatsAppHeader from "@/Components/whatsapp/WhatsAppHeader";
import WhatsAppLayout from "@/Components/whatsapp/WhatsAppLayout";

export default function WhatsAppPage() {
  const [isCollapsed, setIsCollapsed] =
    useState(false);

  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() =>
          setIsCollapsed(!isCollapsed)
        }
      />

      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed
            ? "ml-[90px]"
            : "ml-[270px]"
        }`}
      >
        <div className="p-6 lg:p-8">

          <WhatsAppHeader />

          <div className="mt-6">
            <WhatsAppLayout />
          </div>

        </div>
      </main>
    </div>
  );
}