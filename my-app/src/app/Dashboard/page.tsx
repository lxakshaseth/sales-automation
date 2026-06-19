"use client";

import {
   StatsCards
} from "@/Components/dashboard/StatsCards";
import TopBar from "@/Components/Topbar";
import LiveChatFeed from "@/Components/dashboard/LiveChatFeed";
import Contacts from "@/Components/dashboard/contacts";
import PipelineChart from "@/Components/dashboard/PipelineChart";
import RecentActivities from "@/Components/dashboard/RecentActivities";
import RecentLeads from "@/Components/dashboard/RecentLeads";

export default function Dashboard() {
  return (
    <>
  <TopBar
    title="Dashboard Overview"
    description="Monitor leads, conversations, campaigns, contacts and sales performance."
  />

  <div className="mt-6">
    <StatsCards />
  </div>

  <div className="grid grid-cols-1 xl:grid-cols-[1fr_1fr] gap-4 mt-4">
        <LiveChatFeed />
        <Contacts />
      </div>

      <div className="mt-4 pb-6">
        <PipelineChart />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 mt-4 pb-6">
        <RecentLeads />
        <RecentActivities />
      </div>
    </>
  );
}