"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

import WhatsAppLayout from "@/Components/whatsapp/WhatsAppLayout";

export default function WhatsAppPage() {
  const [isCollapsed, setIsCollapsed] =
    useState(false);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() =>
          setIsCollapsed(!isCollapsed)
        }
      />

      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed
            ? "ml-20"
            : "ml-64"
        }`}
      >
        <div className="p-6 lg:p-8">

          <TopBar
            title="WhatsApp Conversations"
            description="Manage customer conversations, send messages, and track delivery status in real time."
          />

          <div className="mt-6">
            <WhatsAppLayout />
          </div>

        </div>
      </main>
    </div>
  );
}