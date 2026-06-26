"use client";

import { useSidebar } from "../../Components/SideBar";
import Campaigns from "../../Components/Campaigns";
import TopBar from "@/Components/Topbar";

export default function CampaignsPage() {
  const { isCollapsed } = useSidebar();
  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <main className={`flex flex-1 w-full flex-col py-10 px-8 bg-zinc-50 overflow-y-auto transition-all duration-300 ${isCollapsed ? 'md:ml-20' : 'md:ml-64'}`}>
        <div className="max-w-[1600px] w-full mx-auto">
          <TopBar
  title="Campaigns"
  description="Manage and automate your WhatsApp and Email marketing campaigns."
/>
          <Campaigns />
        </div>
      </main>
    </div>
  );
}