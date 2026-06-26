"use client";

import { useEffect } from "react";
import { useSidebar } from "@/Components/SideBar";
import Dashboard from "./Dashboard/page";
// import Integration from "./Integration/page";


import { useRouter } from "next/navigation";

export default function Home() {
  const { isCollapsed } = useSidebar();

  const router = useRouter();
  useEffect(() => {
    const token = sessionStorage.getItem("token")
    if (!token) {
      router.replace("/sign-in")
    }
  }, [router])
  return (
    <div className="flex h-screen bg-zinc-50 font-sans overflow-hidden">
      <main className={`flex flex-1 w-full flex-col py-10 px-8 bg-zinc-50 overflow-y-auto transition-all duration-300 ${isCollapsed ? 'md:ml-20' : 'md:ml-64'}`}>
        <div className="max-w-[1700px] w-full mx-auto">
          <Dashboard />
        </div>
      </main>
    </div>
  );
}