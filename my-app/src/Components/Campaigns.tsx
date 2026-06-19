"use client";

import { motion } from "framer-motion";
import { Megaphone, Mail, MessageCircle, Plus, Search, ChevronLeft, ChevronRight, MoreHorizontal, ArrowUpDown, Pencil, Trash2, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const allCampaigns = [
  { id: 1, name: "Winter Sale Launch", type: "Promotion", status: "Completed", audience: 38460, open: "41%", click: "15%", revenue: "₹1,240", progress: 100, enabled: false },
  { id: 2, name: "New Arrivals Announcement", type: "Stock out", status: "Draft", audience: null, open: "-", click: "-", revenue: "-", progress: 0, enabled: true },
  { id: 3, name: "Holiday Gift Guide", type: "Newsletter", status: "Sending", audience: 25458, open: "13%", click: "0.2%", revenue: "₹280", progress: 80, enabled: false },
  { id: 4, name: "Flash Sale — 24 Hours Only", type: "Automation", status: "Scheduled", audience: 1450, open: "14%", click: "11.5%", revenue: "₹878", progress: 96, enabled: true },
  { id: 5, name: "Customer winback flow", type: "Promotion", status: "Completed", audience: 1250, open: "14%", click: "11.5%", revenue: "₹878", progress: 100, enabled: true },
  { id: 6, name: "Back in stock alert", type: "Stock out", status: "Scheduled", audience: 1150, open: "14%", click: "11.5%", revenue: "₹878", progress: 70, enabled: true },
  { id: 7, name: "Monthly newsletter - Dec...", type: "Newsletter", status: "Sending", audience: 950, open: "14%", click: "11.5%", revenue: "₹878", progress: 20, enabled: false },
  { id: 8, name: "Abandoned cart remember", type: "Promotion", status: "Sending", audience: 848, open: "14%", click: "11.5%", revenue: "₹878", progress: 80, enabled: false },
  { id: 9, name: "New Arrivals Announcement", type: "Automation", status: "Draft", audience: null, open: "-", click: "-", revenue: "-", progress: 0, enabled: false },
  { id: 10, name: "Holiday Gift Guide", type: "Stock out", status: "Scheduled", audience: 548, open: "14%", click: "11.5%", revenue: "₹878", progress: 50, enabled: false },
  { id: 11, name: "Flash Sale — 24 Hours Only", type: "Newsletter", status: "Sending", audience: 254, open: "5%", click: "9%", revenue: "₹458", progress: 80, enabled: false },
  { id: 12, name: "Monthly newsletter - Dec...", type: "Newsletter", status: "Completed", audience: 154, open: "3%", click: "7%", revenue: "₹354", progress: 100, enabled: false },
];

const STATUS_TABS = ["All", "Drafts", "Scheduled", "Sending", "Complete"];
const PAGE_SIZE = 8;

const statusColor: Record<string, string> = {
  Completed: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  Draft: "bg-orange-100 text-orange-600 border border-orange-200",
  Sending: "bg-blue-100 text-blue-600 border border-blue-200",
  Scheduled: "bg-violet-100 text-violet-700 border border-violet-200",
};

export default function Campaigns() {


  const router = useRouter();
  useEffect(() => {
    const token = sessionStorage.getItem("token")
    if (!token) {
      router.replace("/sign-in")
    }
  }, [])


  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("All");
  const [page, setPage] = useState(1);
  const [enabledMap, setEnabledMap] = useState<Record<number, boolean>>(
    () => Object.fromEntries(allCampaigns.map(c => [c.id, c.enabled]))
  );

  function toggleEnabled(id: number) {
    setEnabledMap(prev => ({ ...prev, [id]: !prev[id] }));
  }

  const [openMenuId, setOpenMenuId] = useState<number | null>(null);
  const [editCampaign, setEditCampaign] = useState<typeof allCampaigns[0] | null>(null);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("");
  const [deleteCampaign, setDeleteCampaign] = useState<typeof allCampaigns[0] | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpenMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = allCampaigns.filter(c => {
    const matchSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchTab =
      activeTab === "All" ? true :
        activeTab === "Drafts" ? c.status === "Draft" :
          activeTab === "Scheduled" ? c.status === "Scheduled" :
            activeTab === "Sending" ? c.status === "Sending" :
              activeTab === "Complete" ? c.status === "Completed" : true;
    return matchSearch && matchTab;
  });

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="flex flex-col gap-8">
      {/* Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-4">
        {[
          { title: "Total Active", value: "3", icon: Megaphone, color: "text-violet-500", bg: "bg-violet-100" },
          { title: "Emails Sent", value: "27,000", icon: Mail, color: "text-blue-500", bg: "bg-blue-100" },
          { title: "WhatsApp Msgs", value: "18,210", icon: MessageCircle, color: "text-green-500", bg: "bg-green-100" }
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-white p-6 rounded-2xl border border-zinc-200 shadow-sm flex items-center gap-5"
          >
            <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${stat.bg}`}>
              <stat.icon size={24} className={stat.color} />
            </div>
            <div>
              <h3 className="text-zinc-500 text-sm font-medium">{stat.title}</h3>
              <p className="text-2xl font-bold text-zinc-900 mt-1">{stat.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Search & Filter Bar */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.15 }}
        className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-zinc-200 shadow-sm"
      >
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
          <div className="relative w-full sm:w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all"
            />
          </div>
          <div className="flex bg-zinc-100 p-1 rounded-xl w-full sm:w-auto">
            {["All", "Email", "WhatsApp"].map(f => (
              <button
                key={f}
                className={`flex-1 sm:flex-none px-5 py-2 text-sm font-medium rounded-lg transition-colors ${f === "All" ? "bg-white text-zinc-900 shadow-sm" : "text-zinc-500 hover:text-zinc-700"}`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
        <Link
          href="/Campaign/create-campaign"
          className="w-full sm:w-auto flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-6 py-2.5 rounded-xl font-medium transition-colors shadow-sm shadow-violet-600/20 text-sm"
        >
          <Plus size={16} />
          Create Campaign
        </Link>
      </motion.div>

      {/* Table Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="bg-white rounded-2xl border border-zinc-200 shadow-sm overflow-hidden"
      >
        {/* Tabs */}
        <div className="flex items-center gap-1 px-4 pt-4 border-b border-zinc-100">
          {STATUS_TABS.map(tab => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setPage(1); }}
              className={`px-5 py-2 text-sm font-medium rounded-t-xl transition-colors ${activeTab === tab
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-500 hover:text-zinc-700 hover:bg-zinc-50"
                }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-zinc-100">
          <div className="relative w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-4 py-2 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all"
            />
          </div>
          <select className="text-sm border border-zinc-200 rounded-xl px-3 py-2 bg-zinc-50 text-zinc-600 outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all">
            <option>All statuses</option>
            <option>Completed</option>
            <option>Draft</option>
            <option>Sending</option>
            <option>Scheduled</option>
          </select>
          <select className="text-sm border border-zinc-200 rounded-xl px-3 py-2 bg-zinc-50 text-zinc-600 outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all">
            <option>Last 30 days</option>
            <option>Last 7 days</option>
            <option>Last 90 days</option>
            <option>All time</option>
          </select>
          <span className="text-sm text-zinc-500 ml-auto">Sort by:
            <span className="font-medium text-zinc-700"> Date Created</span>
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-zinc-50 border-b border-zinc-100">
                <th className="w-10 px-4 py-3">
                  <input type="checkbox" className="rounded border-zinc-300 accent-violet-600" />
                </th>
                {[
                  { label: "Campaign", sort: true },
                  { label: "Type", sort: true },
                  { label: "Status", sort: true },
                  { label: "Open", sort: true },
                  { label: "Click", sort: false },
                  { label: "Progress", sort: true },
                  { label: "", sort: false },
                ].map((col) => (
                  <th key={col.label} className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide whitespace-nowrap">
                    <span className="flex items-center gap-1">
                      {col.label}
                      {col.sort && <ArrowUpDown size={11} className="text-zinc-400" />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16 text-zinc-400 text-sm">
                    No campaigns found
                  </td>
                </tr>
              ) : (
                paginated.map((c, i) => (
                  <tr
                    key={c.id}
                    className={`border-b border-zinc-100 hover:bg-zinc-50 transition-colors ${i % 2 === 0 ? "" : "bg-zinc-50/30"}`}
                  >
                    <td className="px-4 py-3">
                      <input type="checkbox" className="rounded border-zinc-300 accent-violet-600" />
                    </td>
                    {/* Campaign name + toggle */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3 min-w-[200px]">
                        <button
                          onClick={() => toggleEnabled(c.id)}
                          style={{ minWidth: "36px" }}
                          className={`h-5 w-9 rounded-full transition-all duration-200 flex-shrink-0 relative ${enabledMap[c.id] ? "bg-violet-600" : "bg-zinc-300"}`}
                        >
                          <span className={`absolute top-[2px] left-[2px] w-[14px] h-[14px] bg-white rounded-full shadow transition-transform duration-200 ${enabledMap[c.id] ? "translate-x-[16px]" : "translate-x-0"}`} />
                        </button>
                        <span className="text-sm font-medium text-zinc-800 truncate max-w-[150px]">{c.name}</span>
                      </div>
                    </td>
                    {/* Type */}
                    <td className="px-4 py-3">
                      <span className="text-sm text-zinc-600">{c.type}</span>
                    </td>
                    {/* Status */}
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${statusColor[c.status] ?? "bg-zinc-100 text-zinc-600"}`}>
                        {c.status}
                      </span>
                    </td>
                    {/* Open */}
                    <td className="px-4 py-3 text-sm text-zinc-700">{c.open}</td>
                    {/* Click */}
                    <td className="px-4 py-3 text-sm text-zinc-700">{c.click}</td>
                    {/* Progress */}
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 min-w-[100px]">
                        <div className="flex-1 h-1.5 bg-zinc-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-violet-500 rounded-full"
                            style={{ width: `${c.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-zinc-500 w-8 text-right">{c.progress}%</span>
                      </div>
                    </td>
                    {/* Actions */}
                    <td className="px-4 py-3">
                      <div className="relative" ref={openMenuId === c.id ? menuRef : null}>
                        <button
                          onClick={() => setOpenMenuId(openMenuId === c.id ? null : c.id)}
                          className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
                        >
                          <MoreHorizontal size={16} />
                        </button>
                        {openMenuId === c.id && (
                          <div className="absolute right-0 top-8 z-50 w-36 bg-white border border-zinc-200 rounded-xl shadow-lg py-1 overflow-hidden">
                            <button
                              onClick={() => { setEditCampaign(c); setEditName(c.name); setEditType(c.type); setOpenMenuId(null); }}
                              className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-zinc-700 hover:bg-zinc-50 transition-colors"
                            >
                              <Pencil size={14} className="text-zinc-400" />
                              Edit
                            </button>
                            <button
                              onClick={() => { setDeleteCampaign(c); setOpenMenuId(null); }}
                              className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
                            >
                              <Trash2 size={14} className="text-red-400" />
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-zinc-100">
          <p className="text-xs text-zinc-400">Metrics update every 15 minutes based on Subscriber interactions</p>
          {totalPages > 1 && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(n => (
                <button
                  key={n}
                  onClick={() => setPage(n)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${page === n ? "bg-zinc-900 text-white" : "text-zinc-500 hover:bg-zinc-100"
                    }`}
                >
                  {n}
                </button>
              ))}
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 transition-colors"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      </motion.div>

      {/* Edit Modal */}
      {editCampaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-zinc-200">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100">
              <h2 className="text-lg font-bold text-zinc-900">Edit Campaign</h2>
              <button onClick={() => setEditCampaign(null)} className="p-1.5 rounded-lg hover:bg-zinc-100 transition-colors">
                <X size={18} className="text-zinc-500" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Campaign Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Type</label>
                <select
                  value={editType}
                  onChange={(e) => setEditType(e.target.value)}
                  className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all bg-white"
                >
                  {["Promotion", "Stock out", "Newsletter", "Automation"].map(t => (
                    <option key={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-zinc-100">
              <button
                onClick={() => setEditCampaign(null)}
                className="px-4 py-2 text-sm border border-zinc-200 rounded-xl hover:bg-zinc-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => setEditCampaign(null)}
                className="px-4 py-2 text-sm bg-violet-600 hover:bg-violet-700 text-white rounded-xl transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirm Dialog */}
      {deleteCampaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-sm shadow-2xl border border-zinc-200">
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
                <Trash2 size={22} className="text-red-500" />
              </div>
              <h2 className="text-lg font-bold text-zinc-900 mb-1">Delete Campaign?</h2>
              <p className="text-sm text-zinc-500">
                <span className="font-semibold text-zinc-700">&ldquo;{deleteCampaign.name}&rdquo;</span> ko delete karne ke baad wapas nahi laya ja sakta.
              </p>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-zinc-100">
              <button
                onClick={() => setDeleteCampaign(null)}
                className="px-4 py-2 text-sm border border-zinc-200 rounded-xl hover:bg-zinc-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => setDeleteCampaign(null)}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-xl transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}