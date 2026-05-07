"use client";

import { UserPlus, Clock } from "lucide-react";
import Link from "next/link";

export default function RecentLeads() {
  return (
    <div 
      className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col overflow-hidden h-[450px]"
    >
      <div 
        className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0"
      >
        <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
          <UserPlus size={18} className="text-blue-500" />
          Contacts
        </h3>
        <div className="flex items-center gap-3">
        <Link href="/Contacts" className="text-xs font-medium text-blue-600 dark:text-blue-400 hover:underline relative z-10">
            View All
          </Link>
        </div>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800 flex flex-col gap-4">
        {[
          { name: "Rahul Sharma", company: "Tech Solutions", time: "2 mins ago", status: "Hot", color: "rose" },
          { name: "Priya Patel", company: "Global Innovators", time: "1 hour ago", status: "Warm", color: "orange" },
          { name: "Amit Kumar", company: "NextGen Systems", time: "3 hours ago", status: "Cold", color: "slate" },
          { name: "Sneha Gupta", company: "Alpha Corp", time: "5 hours ago", status: "Hot", color: "rose" },
          { name: "Vikram Singh", company: "Pioneer Tech", time: "1 day ago", status: "Warm", color: "orange" },
        ].map((lead, i) => (
          <div key={i} className="flex items-center justify-between group">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-600 dark:text-zinc-400 font-medium text-sm border border-zinc-200 dark:border-zinc-700">
                {lead.name.split(' ').map(n => n[0]).join('')}
              </div>
              <div>
                <p className="text-sm font-medium text-zinc-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors cursor-pointer">
                  {lead.name}
                </p>
                <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
                  <span>{lead.company}</span>
                  <span className="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700"></span>
                  <span className="flex items-center gap-1"><Clock size={10} /> {lead.time}</span>
                </div>
              </div>
            </div>
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
              lead.status === 'Hot' ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400' :
              lead.status === 'Warm' ? 'bg-orange-100 text-orange-700 dark:bg-orange-500/10 dark:text-orange-400' :
              'bg-slate-100 text-slate-700 dark:bg-slate-500/20 dark:text-slate-400'
            }`}>
              {lead.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}