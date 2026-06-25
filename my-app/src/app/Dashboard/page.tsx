"use client";

import { DashboardHeader } from "@/Components/dashboard/StatsCards";
import EmailStats from "@/Components/dashboard/EmailStats";
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

          <div className="mt-6 w-full">
            <EmailStats />
          </div>

        </div>
      </main>
    </div>
  );
}