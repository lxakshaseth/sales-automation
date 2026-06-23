"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import SideBar from "@/Components/SideBar";
import EmailStats from "@/Components/dashboard/EmailStats";

export default function DashboardPage() {
  const router = useRouter();
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
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-22.5" : "ml-67.5"
        }`}
      >
        <div className="p-6 lg:p-8">

          {/* Email Stats */}
          <div className="mt-6 pb-8 max-w-3xl">
            <EmailStats />
          </div>

        </div>
      </main>
    </div>
  );
}
