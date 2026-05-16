"use client";

import { useState } from "react";

import SideBar from "@/Components/SideBar";

import HeaderSection from "@/Components/LeadsSalesPipeline/HeaderSection";
import Statscards from "@/Components/LeadsSalesPipeline/Statscards";
import PipelineBoard from "@/Components/LeadsSalesPipeline/PipelineBoard";
import PipelineOverview from "@/Components/LeadsSalesPipeline/PipelineOverview";
import SalesFunnel from "@/Components/LeadsSalesPipeline/SalesFunnel";
import RecentActivities from "@/Components/LeadsSalesPipeline/RecentActivities";


export default function LeadSalesPipelinePage() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="flex min-h-screen bg-[#0b0b0f] overflow-hidden">
      
      {/* SIDEBAR */}
      <SideBar
        isCollapsed={isCollapsed}
        onToggleCollapse={() =>
          setIsCollapsed(!isCollapsed)
        }
      />

      {/* MAIN CONTENT */}
      <main
        className={`flex-1 transition-all duration-300 overflow-y-auto ${
          isCollapsed ? "ml-[90px]" : "ml-[270px]"
        }`}
      >
        <div className="p-6 lg:p-8">
          
          {/* HEADER */}
          <HeaderSection />

          {/* STATS CARDS */}
          <div className="mt-6">
            <Statscards />
          </div>

          {/* PIPELINE BOARD */}
          <div className="mt-6">
            <PipelineBoard />
          </div>

          {/* BOTTOM SECTION */}
<div className="grid grid-cols-1 xl:grid-cols-[0.9fr_1.2fr_0.9fr] gap-5 mt-6">

  {/* PIPELINE OVERVIEW */}
  <div>
    <PipelineOverview />
  </div>

  {/* SALES FUNNEL */}
  <div>
    <SalesFunnel />
  </div>

  {/* RECENT ACTIVITIES */}
  <div>
    <RecentActivities />
  </div>



          </div>
        </div>
      </main>
    </div>
  );
}