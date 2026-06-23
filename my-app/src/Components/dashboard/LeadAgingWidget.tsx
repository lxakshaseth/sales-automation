"use client";

import { useEffect, useState } from "react";

interface LeadAging {
  id: string;
  name: string;
  company: string;
  email: string;
  stage: string;
  lastActivity: string;
  agingDays: number;
}

export default function LeadAgingWidget() {
  const [leads, setLeads] = useState<LeadAging[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/dashboard/lead-aging")
      .then((res) => res.json())
      .then((data) => {
        setLeads(data.data || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getBadgeColor = (days: number) => {
    if (days <= 3) {
      return "bg-green-100 text-green-700 border border-green-300";
    }

    if (days <= 7) {
      return "bg-yellow-100 text-yellow-700 border border-yellow-300";
    }

    if (days <= 14) {
      return "bg-orange-100 text-orange-700 border border-orange-300";
    }

    return "bg-red-100 text-red-700 border border-red-300";
  };

  return (
      <div className="bg-[#beaffc] rounded-xl border border-black p-3 h-[300px] w-[450px] flex flex-col">
      <div className=" mb-2 shrink-0">
        <h2 className="text-lg text-center font-semibold text-black">Lead Tracker</h2>
      </div>

      {loading ? (
        <div className="text-slate-500 text-sm">Loading...</div>
      ) : leads.length === 0 ? (
        <p className="text-slate-500 text-sm">No Leads Found</p>
      ) : (
        <div className="flex-1 overflow-y-auto rounded-2xl border border-slate-500">
          <table
            className="w-full bg-white text-sm table-fixed"
            style={{ borderCollapse: "collapse" }}
          >
            <colgroup>
              <col style={{ width: "42%" }} />
              <col style={{ width: "33%" }} />
              <col style={{ width: "24%" }} />
            </colgroup>
            <thead className="sticky top-0 bg-slate-50 z-10">
              <tr>
                <th className="text-left font-medium  px-6 py-3 border-b border-slate-200">
                  Name
                </th>
                <th className="text-left font-medium  py-3 border-b border-slate-200">
                  Recent Activity
                </th>
                <th className="text-left font-medium  px-8 py-3 border-b border-slate-200">
                  Days
                </th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="border-b border-slate-100 last:border-b-0 hover:bg-slate-50 transition-colors"
                >
                  <td className="px-4 py-3 overflow-hidden">
                    <div className="font-semibold text-slate-900 truncate">
                      {lead.name}
                    </div>
                    <div className="text-xs text-slate-400 truncate">
                      {lead.email}
                    </div>
                  </td>
                  <td className="px-7 py-3 text-xs truncate">
                    {/^email/i.test(lead.lastActivity)
                      ? "Email"
                      : /^sms|^text/i.test(lead.lastActivity)
                      ? "SMS"
                      : lead.lastActivity}
                  </td>
                  <td className="px-4 py-3 text-left">
                    <span
                      className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getBadgeColor(
                        lead.agingDays
                      )}`}
                    >
                      {lead.agingDays} Days
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}