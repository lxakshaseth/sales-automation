"use client";

import { useState,useEffect } from "react";
import SideBar from "@/Components/SideBar";
import {
   StatsCards
} from "@/Components/dashboard/StatsCards";
import LiveChatFeed from "@/Components/dashboard/LiveChatFeed";
import Contacts from "@/Components/dashboard/contacts";
import PipelineChart from "@/Components/dashboard/PipelineChart";
import RecentActivities from "@/Components/dashboard/RecentActivities";
import RecentLeads from "@/Components/dashboard/RecentLeads";
import { useRouter } from "next/navigation";


export default function DashboardPage() {
  const router=useRouter();


  const [isCollapsed, setIsCollapsed] = useState(false);
   useEffect(() => {
    const token = sessionStorage.getItem("token");

    if (!token) {
      router.replace("/sign-in");
    }
  }, [router]);


  
  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">

      {/* Sidebar */}
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() =>
          setIsCollapsed(!isCollapsed)
        }
      />

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-22.5" : "ml-67.5"
        }`}
      >
        <div className="p-6 lg:p-8">

    

          <div className="mt-2">
            <StatsCards />
          </div>

          {/* Live Chat + Contacts */}
          <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-6 mt-6">

            <LiveChatFeed />

            <Contacts />

          </div>

          {/* Pipeline Chart */}
          <div className="mt-6 pb-8">
            <PipelineChart />
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6 pb-8">
  <RecentLeads />
  <RecentActivities />
</div>
        </div>
      </main>
    </div>
  );
}