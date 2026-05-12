"use client";

import { UserPlus, MessageSquare, BookUser, Rocket } from "lucide-react";
import PipelineChart from "./PipelineChart";
import LiveChatFeed from "./LiveChatFeed";
import RecentLeads from "./RecentLeads";

export default function Dashboard() {
  const stats = [
    {
      title: "Our Leads",
      value: "1,240",
      change: "+12.5%",
      isPositive: true,
      icon: UserPlus,
      color: "bg-blue-500",
    },
    {
      title: "Live Chat Feed",
      value: "342",
      change: "+5.2%",
      isPositive: true,
      icon: MessageSquare,
      color: "bg-emerald-500",
    },
    {
      title: "Contacts",
      value: "8,549",
      change: "+2.4%",
      isPositive: true,
      icon: BookUser,
      color: "bg-violet-500",
    },
    {
      title: "Campaigns",
      value: "12",
      change: "+2 Active",
      isPositive: true,
      icon: Rocket,
      color: "bg-orange-500",
    },
  ];

  return (
    <div className="flex flex-col gap-8">
      {/* Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shadow-inner ${stat.color}`}>
                  <Icon size={24} />
                </div>
                <span className={`text-sm font-medium px-2.5 py-1 rounded-full ${stat.isPositive ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400'}`}>
                  {stat.change}
                </span>
              </div>
              <h3 className="text-zinc-500 dark:text-zinc-400 text-sm font-medium">{stat.title}</h3>
              <p className="text-2xl font-bold text-zinc-900 dark:text-white mt-1">{stat.value}</p>
            </div>
          );
        })}
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Live Chat Feed */}
        <LiveChatFeed />

        {/* Recent Leads / Activity */}
        <RecentLeads />

      </div>

      <PipelineChart />
    </div>
  );
}