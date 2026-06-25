"use client";

import { DashboardHeader } from "@/Components/dashboard/StatsCards";
import LeadAgingWidget from "@/Components/dashboard/LeadAgingWidget";
import EmailStats from "@/Components/dashboard/EmailStats";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Megaphone, Users, MessageCircle, FileText } from "lucide-react";

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

          <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Campaigns */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm p-4 flex flex-col gap-3 transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-orange-100">
                  <Megaphone className="w-5 h-5 text-orange-600" />
                </div>
                <p className="text-sm text-gray-600">Campaigns</p>
              </div>
            </div>

            {/* Template */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm p-4 flex flex-col gap-3 transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-purple-100">
                  <FileText className="w-5 h-5 text-purple-600" />
                </div>
                <p className="text-sm text-gray-600">Template</p>
              </div>
            </div>

            {/* Leads */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm p-4 flex flex-col gap-3 transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-blue-100">
                  <Users className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-sm text-gray-600">Leads</p>
              </div>
            </div>
            
            {/* WhatsApp Contact */}
            <div className="rounded-2xl bg-white border border-gray-200 shadow-sm p-4 flex flex-col gap-3 transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-emerald-100">
                  <MessageCircle className="w-5 h-5 text-emerald-600" />
                </div>
                <p className="text-sm text-gray-600">WhatsApp Contact</p>
              </div>
            </div>
          </div>
        <div className="mt-6 w-full grid grid-cols-1 lg:grid-cols-2 gap-6">
          <EmailStats />
          <LeadAgingWidget />
        </div>

        </div>
      </main>
    </div>
  );
}