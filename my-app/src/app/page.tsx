"use client";

import { useState } from "react";
import Sidebar from "../Components/SideBar";
import Dashboard from "../Components/Dashboard";
import Integration from "../Components/Integration";

export default function Home() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans dark:bg-zinc-950 overflow-hidden">
      <Sidebar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />
      <main className={`flex flex-1 w-full flex-col py-10 px-8 bg-zinc-50 dark:bg-zinc-950 overflow-y-auto transition-all duration-300 ${isCollapsed ? 'md:ml-20' : 'md:ml-64'}`}>
        <div className="max-w-7xl w-full mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-zinc-900 dark:text-white tracking-tight">Dashboard Overview</h1>
            <p className="text-zinc-500 dark:text-zinc-400 mt-2"></p>
          </div>

          <Dashboard />
        </div>
      </main>
    </div>
  );
}