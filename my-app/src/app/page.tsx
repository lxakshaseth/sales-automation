"use client";

import { useState } from "react";
import Sidebar from "../Components/SideBar";
import Dashboard from "./Dashboard/page";
import Integration from "./Integration/page";

export default function Home() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <Sidebar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
      />
      <main className={`flex flex-1 w-full flex-col py-10 px-8 bg-zinc-50 overflow-y-auto transition-all duration-300 ${isCollapsed ? 'md:ml-20' : 'md:ml-64'}`}>
        <div className="max-w-7xl w-full mx-auto">
          <Dashboard />
        </div>
      </main>
    </div>
  );
}