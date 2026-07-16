"use client";

import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";


export default function RecentAdminActivities() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);
  const [autoDeleted, setAutoDeleted] = useState(false);
  const [fromDate, setFromDate] = useState("");  
  const [toDate, setToDate] = useState("");
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const closeNotification = () => {
  setAutoDeleted(false);
  localStorage.removeItem("auditAutoDelete");
};

  useEffect(() => {
    fetchLogs();
  }, []);

  useEffect(() => {
  const saved = localStorage.getItem("auditAutoDelete");

  if (!saved) return;

  const data = JSON.parse(saved);

  if (Date.now() < data.expiry) {
    setAutoDeleted(true);
  } else {
    localStorage.removeItem("auditAutoDelete");
  }
}, []);

  async function fetchLogs() {
    try {
      const res = await fetch("/api/audit-logs/recent");
      const data = await res.json();

      if (data.success) {
    setLogs(data.data);

   if (data.autoDeleted) {
  const expiry = Date.now() + 24 * 60 * 60 * 1000;

  localStorage.setItem("auditAutoDelete", JSON.stringify({
    show: true,
    expiry,
  }));

  setAutoDeleted(true);
}
  }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  const deleteLogs = () => {
  if (!fromDate || !toDate) return;

  setShowDeleteModal(true);
};

const confirmDelete = async () => {
  try {
    const res = await fetch("/api/audit-logs/recent", {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        fromDate,
        toDate,
      }),
    });

    const data = await res.json();

    if (data.success) {
      fetchLogs();
      setShowDeleteModal(false);
    }
  } catch (err) {
    console.error(err);
  }
};

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

  const renderTable = () => (
    <table className="w-full text-sm">
      <thead className="bg-white border-b border-zinc-100 sticky top-0 z-10">
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
          logs
          .filter((log) => {
            if (!fromDate || !toDate) return true;

            const logDate = new Date(log.createdAt);

            const startDate = new Date(fromDate);

            const endDate = new Date(toDate);
            endDate.setHours(23, 59, 59, 999);

            return logDate >= startDate && logDate <= endDate;
          })
          .map((log) => (
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

              <td className="px-4 py-4 text-zinc-600">{log.details}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );

  return (
    <>
      {/* Main Card */}
      <div className="bg-white rounded-2xl border border-gray-300 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
        {/* Header */}
        {autoDeleted && (
        <div className="mx-4 mt-3 flex items-start justify-between rounded-xl border border-green-200 bg-green-50 px-4 py-3">

          <p className="text-sm text-green-700">
            ✔ 6-month-old audit logs were automatically deleted successfully.
          </p>

          <button
            onClick={closeNotification}
            className="ml-4 text-green-600 hover:text-green-800 text-lg leading-none"
          >
            ✕
          </button>

        </div>
      )}
        <div className="p-4 border-b border-zinc-200 flex items-center justify-between">
          <h3 className="font-semibold text-zinc-900 flex items-center gap-2">
            <ShieldCheck size={18} className="text-violet-600" />
            Recent Admin Activities
          </h3>

         <div className="flex items-center gap-2">

          <div className="flex items-center gap-1.5">
            <label htmlFor="audit-from-date" className="text-xs font-medium text-zinc-500">
              From
            </label>
            <input
              id="audit-from-date"
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="border border-violet-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <label htmlFor="audit-to-date" className="text-xs font-medium text-zinc-500">
              To
            </label>
            <input
              id="audit-to-date"
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="border border-violet-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          <button
            className="text-xs font-medium text-violet-600 hover:text-violet-700"
            onClick={deleteLogs}
          >
            Delete
          </button>

          <button
            onClick={() => setShowAll(true)}
            className="text-xs font-medium text-violet-600 hover:text-violet-700"
          >
            View All
          </button>

        </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto overflow-y-auto max-h-[300px]">
          {renderTable()}
        </div>
      </div>

      {/* View All Modal */}
      {showAll && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-6"
          onClick={() => setShowAll(false)}
        >
          <div
            className="bg-white rounded-2xl p-4 shadow-sm flex flex-col w-full max-w-7xl h-[85vh] min-h-0"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3 px-1 border-b border-zinc-200 pb-3 shrink-0">
              <h3 className="font-semibold text-zinc-900 flex items-center gap-2">
                <ShieldCheck size={18} className="text-violet-600" />
                Recent Admin Activities
              </h3>

              <button
                onClick={() => setShowAll(false)}
                className="text-xs font-medium text-gray-500 hover:text-gray-800 border border-gray-300 rounded-full w-7 h-7 flex items-center justify-center shrink-0"
              >
                ✕
              </button>
            </div>

            {/* Full Table */}
            <div className="rounded-xl border border-zinc-100 overflow-auto flex-1 min-h-0">
              {renderTable()}
            </div>
          </div>
        </div>
      )}
          {showDeleteModal && (
      <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl w-[420px] shadow-2xl p-6">

          <h2 className="text-lg font-semibold text-zinc-900">
            Delete Audit Logs
          </h2>

          <p className="mt-3 text-sm text-zinc-600">
            Are you sure you want to delete the selected audit logs?
          </p>

          <div className="mt-4 bg-zinc-100 rounded-lg px-3 py-2 text-sm">
            {fromDate} → {toDate}
          </div>

          <p className="mt-3 text-xs text-red-500">
            This action cannot be undone.
          </p>

          <div className="mt-6 flex justify-end gap-3">

            <button
              onClick={() => setShowDeleteModal(false)}
              className="px-4 py-2 rounded-lg border border-zinc-300"
            >
              Cancel
            </button>

            <button
              onClick={confirmDelete}
              className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
            >
              Delete
            </button>

          </div>

        </div>
      </div>
    )}
    </>
  );
}