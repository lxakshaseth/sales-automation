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
  const [showAll, setShowAll] = useState(false);

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
      return "bg-green-50 text-green-600 border border-green-200";
    }
    if (days <= 7) {
      return "bg-yellow-50 text-yellow-600 border border-yellow-200";
    }
    if (days <= 14) {
      return "bg-orange-50 text-orange-600 border border-orange-200";
    }
    return "bg-red-50 text-red-600 border border-red-200";
  };

  const renderTable = (leadsToRender: LeadAging[]) => (
    <table
      className="w-full text-sm table-fixed"
      style={{ borderCollapse: "collapse" }}
    >
      <colgroup>
        <col style={{ width: "42%" }} />
        <col style={{ width: "33%" }} />
        <col style={{ width: "25%" }} />
      </colgroup>
      <thead className="sticky top-0 bg-gray-50 z-10">
        <tr>
          <th className="text-left font-medium text-gray-400 text-xs px-4 py-2.5">
            Name
          </th>
          <th className="text-left font-medium text-gray-400 text-xs py-2.5">
            Recent Activity
          </th>
          <th className="text-left font-medium text-gray-400 text-xs px-7 py-2.5">
            Days
          </th>
        </tr>
      </thead>
      <tbody>
        {leadsToRender.map((lead) => (
          <tr
            key={lead.id}
            className="border-t border-gray-100 hover:bg-gray-50/60 transition-colors"
          >
            <td className="px-4 py-3 overflow-hidden">
              <div className="font-semibold text-gray-900 truncate text-sm">
                {lead.name}
              </div>
              <div className="text-xs text-gray-400 truncate">
                {lead.email}
              </div>
            </td>
            <td className="py-3 text-sm text-gray-600 truncate">
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
  );

return (
    <>
      <div className="bg-white border border-gray-500 rounded-2xl p-4 shadow-sm flex flex-col w-full h-[320px] sm:h-[360px] min-h-0 min-w-0 relative transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
        {/* Header */}
        <div className="flex items-center justify-between mb-3 px-1 shrink-0">
          <h2 className="text-base font-semibold text-gray-900">
            Lead Tracker
          </h2>
          <button
            onClick={() => setShowAll(true)}
            className="text-xs font-medium text-violet-600 hover:text-violet-700"
          >
            View All
          </button>
        </div>

        {loading ? (
          <div className="text-slate-400 text-sm px-1 py-4">Loading...</div>
        ) : leads.length === 0 ? (
          <p className="text-slate-400 text-sm px-1 py-4">No Leads Found</p>
        ) : (
          <div className="rounded-xl border border-gray-100 overflow-y-auto flex-1 min-h-0">
            {renderTable(leads)}
          </div>
        )}
      </div>

      {/* View All Modal */}
      {showAll && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-6"
          onClick={() => setShowAll(false)}
        >
          <div
            className="bg-white rounded-2xl p-4 shadow-sm flex flex-col w-full max-w-3xl h-[85vh] min-h-0"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3 px-1 shrink-0">
              <h2 className="text-base font-semibold text-gray-900">
                Lead Tracker
              </h2>
              <button
                onClick={() => setShowAll(false)}
                className="text-xs font-medium text-gray-500 hover:text-gray-800 border border-gray-300 rounded-full w-7 h-7 flex items-center justify-center shrink-0"
              >
                ✕
              </button>
            </div>

            {loading ? (
              <div className="text-slate-400 text-sm px-1 py-4">
                Loading...
              </div>
            ) : leads.length === 0 ? (
              <p className="text-slate-400 text-sm px-1 py-4">
                No Leads Found
              </p>
            ) : (
              <div className="rounded-xl border border-gray-100 overflow-y-auto flex-1 min-h-0">
                {renderTable(leads)}
              </div>
            )}
          </div>
        </div>
      )}
    </>
);
}