"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardHeader } from "@/Components/dashboard/StatsCards";
import EmailStats from "@/Components/dashboard/EmailStats";
import LeadFunnelChart from "@/Components/dashboard/LeadFunnelChart";
import { fetchLeadFunnel, formatDateRangeLabel, FunnelItem } from "@/services/leadFunnel.service";

export default function DashboardPage() {
  const router = useRouter();
  const [timePeriod, setTimePeriod] = useState<"7" | "30">("7");
  const [funnelData, setFunnelData] = useState<FunnelItem[]>([]);
  const [dateRangeLabel, setDateRangeLabel] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem("token");
    if (!token) {
      router.replace("/sign-in");
    }
  }, [router]);

  useEffect(() => {
    async function loadFunnel() {
      setLoading(true);
      try {
        const res = await fetchLeadFunnel(timePeriod);
        setFunnelData(res.data);
        setDateRangeLabel(formatDateRangeLabel(res.date_range.from, res.date_range.to));
      } catch (err) {
        console.error("Failed to load funnel data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadFunnel();
  }, [timePeriod]);

  return (
    <div className="min-h-screen w-full">
      <main className="w-full">
        <div className="w-full">
          <DashboardHeader />

          <div className="mt-6 w-full">
            <EmailStats />
          </div>

          {/* Lead Funnel Widget */}
          <div className="mt-6 pb-8">
            {loading ? (
              <div className="bg-white border border-[#e8edf5] rounded-[20px] shadow-sm p-5 h-[360px] flex items-center justify-center text-[#94a3b8] text-[14px]">
                Loading funnel data...
              </div>
            ) : (
              <LeadFunnelChart
                data={funnelData}
                timePeriod={timePeriod}
                onTimePeriodChange={setTimePeriod}
                dateRangeLabel={dateRangeLabel}
              />
            )}
          </div>

        </div>
      </main>
    </div>
  );
}