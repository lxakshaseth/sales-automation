"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSidebar } from "@/Components/SideBar";
import { DashboardHeader } from "@/Components/dashboard/StatsCards";
import EmailStats from "@/Components/dashboard/EmailStats";
import LeadFunnelChart from "@/Components/dashboard/LeadFunnelChart";
import RecentAdminActivities from "@/Components/dashboard/RecentAdminActivities";
import {
  fetchLeadFunnel,
  formatDateRangeLabel,
  FunnelItem,
} from "@/services/leadFunnel.service";
import { Megaphone, Users, MessageCircle, FileText } from "lucide-react";
import LeadAgingWidget from "@/Components/dashboard/LeadAgingWidget";
import {
  fetchDashboardStats,
  DashboardStats,
} from "@/services/dashboard.service";

export default function DashboardPage() {
  const router = useRouter();
  const { isCollapsed } = useSidebar();
  const [timePeriod, setTimePeriod] = useState<"7" | "30">("7");
  const [funnelData, setFunnelData] = useState<FunnelItem[]>([]);
  const [dateRangeLabel, setDateRangeLabel] = useState("");
  const [loading, setLoading] = useState(true);

  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    campaigns: 0,
    templates: 0,
    leads: 0,
    whatsappContacts: 0,
  });

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
        setDateRangeLabel(
          formatDateRangeLabel(res.date_range.from, res.date_range.to),
        );
      } catch (err) {
        console.error("Failed to load funnel data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadFunnel();
  }, [timePeriod]);

  useEffect(() => {
    async function loadDashboardStats() {
      try {
        const stats = await fetchDashboardStats();
        setDashboardStats(stats);
      } catch (err) {
        console.error("Failed to load dashboard stats:", err);
      }
    }

    loadDashboardStats();
  }, []);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <main className={`flex flex-1 w-full flex-col py-10 px-8 bg-zinc-50 overflow-y-auto transition-all duration-300 ${isCollapsed ? 'md:ml-20' : 'md:ml-64'}`}>
        <div className="max-w-[1700px] w-full mx-auto">
          <DashboardHeader />

          {/* Quick Access Cards */}
          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Campaigns */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm px-6 py-5 min-h-[120px] flex items-center transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-orange-100">
                  <Megaphone className="w-6 h-6 text-orange-600" />
                </div>

                <div>
                  <h3 className="text-3xl font-bold leading-none text-gray-900">
                    {dashboardStats.campaigns}
                  </h3>
                  <p className="mt-2 text-[15px] font-medium text-gray-700">
                    Campaigns
                  </p>
                </div>
              </div>
            </div>

            {/* Leads */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm px-6 py-5 min-h-[120px] flex items-center transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-blue-100">
                  <Users className="w-6 h-6 text-blue-600" />
                </div>

                <div>
                  <h3 className="text-3xl font-bold leading-none text-gray-900">
                    {dashboardStats.leads}
                  </h3>
                  <p className="mt-2 text-[15px] font-medium text-gray-700">
                    Leads
                  </p>
                </div>
              </div>
            </div>

            {/* Templates */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm px-6 py-5 min-h-[120px] flex items-center transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-purple-100">
                  <FileText className="w-6 h-6 text-purple-600" />
                </div>

                <div>
                  <h3 className="text-3xl font-bold leading-none text-gray-900">
                    {dashboardStats.templates}
                  </h3>
                  <p className="mt-2 text-[15px] font-medium text-gray-700">
                    Templates
                  </p>
                </div>
              </div>
            </div>

            {/* WhatsApp Contacts */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm px-6 py-5 min-h-[120px] flex items-center transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center bg-emerald-100">
                  <MessageCircle className="w-6 h-6 text-emerald-600" />
                </div>

                <div>
                  <h3 className="text-3xl font-bold leading-none text-gray-900">
                    {dashboardStats.whatsappContacts}
                  </h3>
                  <p className="mt-2 text-[15px] font-medium text-gray-700">
                    WhatsApp Contacts
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Email Stats + Lead Aging */}
          <div className="mt-6 w-full grid grid-cols-1 lg:grid-cols-2 gap-6">
            <EmailStats />
            <LeadAgingWidget />
          </div>

          {/* Recent Activities */}
          <div className="mt-4 pb-6">
            <RecentAdminActivities />
          </div>

          {/* Lead Funnel Widget */}
          <div className="mt-6 pb-8">
            {loading ? (
              <div className="bg-gray-50 border border-gray-500 rounded-xl shadow-sm p-5 h-[360px] flex items-center justify-center text-[#94a3b8] text-[14px]">
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