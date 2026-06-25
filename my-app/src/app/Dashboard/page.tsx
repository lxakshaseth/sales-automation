"use client";

import { DashboardHeader } from "@/Components/dashboard/StatsCards";
import LeadAgingWidget from "@/Components/dashboard/LeadAgingWidget";
import EmailStats from "@/Components/dashboard/EmailStats";
import RecentAdminActivities from "@/Components/dashboard/RecentAdminActivities";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    const token = sessionStorage.getItem("token");

    if (!token) {
      router.replace("/sign-in");
    }
  }, [router]);

  return (
    <div className="min-h-screen w-full">
      <main className="w-full">
        <div className="w-full">
          <DashboardHeader />

        <div className="mt-6 w-full grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EmailStats />
          <LeadAgingWidget />
        </div>

         <div className="mt-4 pb-6">
        <RecentAdminActivities />
      </div>

        </div>
      </main>
    </div>
  );
}