"use client";

import {
  DashboardHeader
} from "@/Components/dashboard/StatsCards";
import LeadAgingWidget from "@/Components/dashboard/LeadAgingWidget";

export default function Dashboard() {
  return (
    <>
      <DashboardHeader />
      <div className="mt-4 pb-6">
        <LeadAgingWidget />
      </div>
    </>
  );
}