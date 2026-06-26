"use client";

import { useSidebar } from "@/Components/SideBar";
import TopBar from "@/Components/Topbar";

import StatsCards from "@/Components/userManagement/StatsCards";
import UsersTable from "@/Components/userManagement/UsersTable";
import RoleManagement from "@/Components/userManagement/RoleManagement";
import RecentActivity from "@/Components/userManagement/RecentActivity";

export default function UserManagementPage() {
  const { isCollapsed } = useSidebar();
  return (
    <div className="flex min-h-screen bg-[#f8fafc] overflow-hidden">

      {/* MAIN CONTENT */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-[90px]" : "ml-[270px]"
        }`}
      >
        <div className="p-6 lg:p-8">

          {/* TOPBAR */}
          <TopBar
            title="User Management"
            description="Handle users, permissions, roles, access control, authentication, and team monitoring."
          />

          {/* STATS */}
          <div className="mt-6">
            <StatsCards />
          </div>

          {/* USERS TABLE */}
          <div className="mt-6">
            <UsersTable />
          </div>

          {/* ROLE MANAGEMENT + RECENT ACTIVITY */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mt-6">

            <RoleManagement />

            <RecentActivity />

          </div>

        </div>
      </main>
    </div>
  );
}