"use client";

import { motion, Variants } from "framer-motion";
import { Megaphone, Mail, MessageCircle, Plus, Search, Play, Pause, BarChart2 } from "lucide-react";
import { useState } from "react";
import Link from "next/link";

const campaigns = [
  { id: 1, name: "Summer Sale 2024", type: "Email", status: "Active", sent: "12,450", engagement: "24%", date: "Aug 15 - Sep 01" },
  { id: 2, name: "Cart Abandonment", type: "WhatsApp", status: "Active", sent: "3,210", engagement: "68%", date: "Ongoing" },
  { id: 3, name: "Welcome Series", type: "Email", status: "Paused", sent: "8,920", engagement: "42%", date: "Ongoing" },
  { id: 4, name: "VIP Early Access", type: "WhatsApp", status: "Draft", sent: "-", engagement: "-", date: "Sep 10 - Sep 15" },
  { id: 5, name: "Post-Purchase Review", type: "Email", status: "Active", sent: "5,630", engagement: "31%", date: "Ongoing" },
  { id: 6, name: "Flash Promo", type: "WhatsApp", status: "Completed", sent: "15,000", engagement: "55%", date: "Jul 01 - Jul 03" },
];

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export default function Campaigns() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filter, setFilter] = useState("All");

  const filteredCampaigns = campaigns.filter(c => {
    const matchesSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filter === "All" || c.type === filter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="flex flex-col gap-8">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { title: "Total Active", value: "3", icon: Megaphone, color: "text-violet-500", bg: "bg-violet-100 dark:bg-violet-500/20" },
          { title: "Emails Sent", value: "27,000", icon: Mail, color: "text-blue-500", bg: "bg-blue-100 dark:bg-blue-500/20" },
          { title: "WhatsApp Msgs", value: "18,210", icon: MessageCircle, color: "text-green-500", bg: "bg-green-100 dark:bg-green-500/20" }
        ].map((stat, i) => (
          <motion.div 
            key={i} 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-white dark:bg-zinc-900 p-6 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex items-center gap-5"
          >
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${stat.bg}`}>
              <stat.icon size={24} className={stat.color} />
            </div>
            <div>
              <h3 className="text-zinc-500 dark:text-zinc-400 text-sm font-medium">{stat.title}</h3>
              <p className="text-2xl font-bold text-zinc-900 dark:text-white mt-1">{stat.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Actions & Filters */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm"
      >
        <div className="flex flex-col sm:flex-row items-center gap-4 w-full md:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
            <input 
              type="text" 
              placeholder="Search campaigns..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all"
            />
          </div>
          <div className="flex bg-zinc-100 dark:bg-zinc-950 p-1 rounded-xl w-full sm:w-auto">
            {["All", "Email", "WhatsApp"].map(f => (
              <button 
                key={f}
                onClick={() => setFilter(f)}
                className={`flex-1 sm:flex-none px-5 py-2 text-sm font-medium rounded-lg transition-colors ${filter === f ? 'bg-white dark:bg-zinc-800 text-zinc-900 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'}`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <Link href="/Campaign/create" className="w-full md:w-auto flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-6 py-2.5 rounded-xl font-medium transition-colors shadow-sm shadow-violet-600/20">
          <Plus size={18} />
          Create Campaign
        </Link>
      </motion.div>

      {/* Campaigns Grid */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6"
      >
        {filteredCampaigns.map(campaign => (
          <motion.div 
            key={campaign.id}
            variants={itemVariants}
            className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm overflow-hidden flex flex-col group hover:shadow-xl hover:shadow-zinc-200/40 dark:hover:shadow-black/40 transition-all duration-300"
          >
            <div className="p-6 border-b border-zinc-100 dark:border-zinc-800 flex-1">
              <div className="flex justify-between items-start mb-5">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center text-white shadow-sm ${campaign.type === 'WhatsApp' ? 'bg-green-500' : 'bg-blue-500'}`}>
                  {campaign.type === 'WhatsApp' ? <MessageCircle size={22} /> : <Mail size={22} />}
                </div>
                <span className={`px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-full ${
                  campaign.status === 'Active' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400' :
                  campaign.status === 'Paused' ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400' :
                  campaign.status === 'Completed' ? 'bg-blue-100 text-blue-700 dark:bg-blue-500/20 dark:text-blue-400' :
                  'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-400'
                }`}>
                  {campaign.status}
                </span>
              </div>
              <h3 className="text-xl font-bold text-zinc-900 dark:text-white mb-1 group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">{campaign.name}</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">{campaign.date}</p>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-zinc-50 dark:bg-zinc-950 p-4 rounded-xl border border-zinc-200/50 dark:border-zinc-800/50">
                  <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-1 uppercase tracking-wider">Sent</p>
                  <p className="text-xl font-bold text-zinc-900 dark:text-white">{campaign.sent}</p>
                </div>
                <div className="bg-zinc-50 dark:bg-zinc-950 p-4 rounded-xl border border-zinc-200/50 dark:border-zinc-800/50">
                  <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-1 uppercase tracking-wider">{campaign.type === 'WhatsApp' ? 'Read Rate' : 'Open Rate'}</p>
                  <p className="text-xl font-bold text-zinc-900 dark:text-white flex items-center gap-1.5">
                    {campaign.engagement}
                    {campaign.engagement !== '-' && <BarChart2 size={16} className="text-emerald-500" />}
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-zinc-50/50 dark:bg-zinc-900/50 p-4 flex justify-between items-center shrink-0">
              <div className="flex gap-2">
                {campaign.status === 'Active' ? (
                  <button className="p-2 text-zinc-500 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-500/10 rounded-lg transition-colors" title="Pause">
                    <Pause size={18} />
                  </button>
                ) : (
                  <button className="p-2 text-zinc-500 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 rounded-lg transition-colors" title="Start">
                    <Play size={18} />
                  </button>
                )}
              </div>
              <button className="text-sm font-semibold text-violet-600 dark:text-violet-400 hover:text-violet-700 dark:hover:text-violet-300">
                View Report &rarr;
              </button>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}