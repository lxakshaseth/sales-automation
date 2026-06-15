"use client";

import { Megaphone, Calendar, MoreVertical } from "lucide-react";

const campaigns = [
  {
    id: "c1",
    name: "Welcome Series",
    channel: "Email",
    schedule: "Daily",
    status: "Active",
  },
  {
    id: "c2",
    name: "Re-engagement",
    channel: "WhatsApp",
    schedule: "Weekly",
    status: "Paused",
  },
  {
    id: "c3",
    name: "Holiday Promo",
    channel: "Email",
    schedule: "One-time",
    status: "Draft",
  },
];

export default function Campaigns() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mt-6">
      {campaigns.map((c) => (
        <div key={c.id} className="bg-white border border-[#e5e7eb] rounded-3xl p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-[#7c3aed] to-[#9333ea] flex items-center justify-center text-white">
                <Megaphone size={18} />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-[#111827]">{c.name}</h3>
                <p className="text-sm text-[#64748b]">{c.channel} • {c.schedule}</p>
              </div>
            </div>

            <MoreVertical size={18} className="text-[#94a3b8]" />
          </div>

          <div className="mt-6 flex items-center justify-between">
            <div className="flex items-center gap-3 text-[#64748b]">
              <Calendar size={16} />
              <span className="text-sm">{c.schedule}</span>
            </div>

            <div className={`px-3 py-1 rounded-full text-sm font-medium ${c.status === 'Active' ? 'bg-green-100 text-green-700' : c.status === 'Paused' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-700'}`}>
              {c.status}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
