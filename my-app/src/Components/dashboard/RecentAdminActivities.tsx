"use client";

import { ShieldCheck } from "lucide-react";

import { useEffect, useState } from "react";

export default function RecentAdminActivities() {

const [logs, setLogs] = useState<any[]>([]);
const [loading, setLoading] = useState(true);
const [showAll, setShowAll] = useState(false);

useEffect(() => {
  fetchLogs();
}, []);

async function fetchLogs() {
  try {
    const res = await fetch("/api/audit-logs/recent");
    const data = await res.json();

    if (data.success) {
      setLogs(data.data);
    }
  } catch (error) {
    console.error(error);
  } finally {
    setLoading(false);
  }
}

  const getBadgeColor = (action: string) => {
    switch (action) {
      case "Create":
        return "bg-green-100 text-green-700";
      case "Update":
        return "bg-blue-100 text-blue-700";
      case "Delete":
        return "bg-red-100 text-red-700";
      case "Import":
        return "bg-purple-100 text-purple-700";
      default:
        return "bg-zinc-100 text-zinc-700";
    }
  };

  const displayedLogs = showAll
  ? logs
  : logs.slice(0, 5);

  return (
   <div className="bg-white rounded-2xl border border-black-200 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
        <h3 className="font-semibold text-zinc-900 flex items-center gap-2">
          <ShieldCheck size={18} className="text-violet-600" />
          Recent Admin Activities
        </h3>

        <button
        onClick={() => setShowAll(!showAll)}
        className="text-[13px] font-medium text-[#8B5CF6]"
      >
        {showAll ? "View Less" : "View All"}
      </button>
        
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-white border-b border-zinc-100">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Date & Time
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Module
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Action
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Item
              </th>
              <th className="px-4 py-3 text-left font-medium text-zinc-500">
                Details
              </th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
                <tr>
                <td colSpan={5} className="text-center py-6 text-zinc-500">
                    Loading...
                </td>
                </tr>
            ) : logs.length === 0 ? (
                <tr>
                <td colSpan={5} className="text-center py-6 text-zinc-500">
                    No activities found
                </td>
                </tr>
            ) : (
                displayedLogs.map((log) => (
                <tr
                    key={log._id}
                    className="border-b border-zinc-50 hover:bg-violet-50 hover:shadow-sm transition-all duration-200 cursor-pointer"
                >
                    <td className="px-4 py-4 whitespace-nowrap">
                    {new Date(log.createdAt).toLocaleString("en-GB", {
                        day: "2-digit",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                    })}
                    </td>

                    <td className="px-4 py-4">{log.module}</td>

                    <td className="px-4 py-4">
                    <span
                        className={`px-2.5 py-1 rounded-full text-xs font-medium ${getBadgeColor(
                        log.action
                        )}`}
                    >
                        {log.action}
                    </span>
                    </td>

                    <td className="px-4 py-4 font-medium text-zinc-900">
                    {log.item}
                    </td>

                    <td className="px-4 py-4 text-zinc-600">
                    {log.details}
                    </td>
                </tr>
                ))
            )}
            </tbody>
        </table>
      </div>
    </div>
  );
}