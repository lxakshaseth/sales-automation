"use client";

import { useEffect, useState } from "react";
import Sidebar from "../Components/SideBar";
import Dashboard from "./Dashboard/page";
// import Integration from "./Integration/page";


import { useRouter } from "next/navigation";

export default function Home() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const router = useRouter();
  useEffect(() => {
    const token = sessionStorage.getItem("token")
    if (!token) {
      router.replace("/sign-in")
    }
  }, [router])







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