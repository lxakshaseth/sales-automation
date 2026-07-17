"use client";

import { ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";

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

          localStorage.setItem(
            "auditAutoDelete",
            JSON.stringify({
              show: true,
              expiry,
            }),
          );

          setAutoDeleted(true);
        }
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  const openDeleteModal = () => {
    setFromDate("");
    setToDate("");
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!fromDate || !toDate) {
      toast.error("Please select both From and To dates.");
      return;
    }

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
        toast.success("Audit logs deleted successfully.");

        setShowDeleteModal(false);
        setFromDate("");
        setToDate("");

        fetchLogs();
      } else {
        toast.error(data.message || "Failed to delete audit logs.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Something went wrong. Please try again.");
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
          logs.map((log) => (
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
                    log.action,
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
      <div className="bg-white rounded-2xl border border-gray-300 shadow-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
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

          <div className="flex items-center gap-3">
            <button
              onClick={openDeleteModal}
              className="text-xs font-medium text-red-600 hover:text-red-700"
            >
              Delete Logs
            </button>

            <button
              onClick={() => setShowAll(true)}
              className="text-xs font-medium text-violet-600 hover:text-violet-700"
            >
              View All
            </button>
          </div>
        </div>

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

            {/* Table */}
            <div className="rounded-xl border border-zinc-100 overflow-auto flex-1 min-h-0">
              {renderTable()}
            </div>
          </div>
        </div>
      )}

      {/* Delete Logs Modal */}
      {showDeleteModal && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-6"
          onClick={() => setShowDeleteModal(false)}
        >
          <div
            className="bg-white rounded-2xl w-full max-w-md shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-semibold text-zinc-900">
              Delete Audit Logs
            </h2>

            <p className="mt-2 text-sm text-zinc-600">
              Select the date range of audit logs you want to permanently
              delete.
            </p>

            <div className="mt-6 space-y-4">
              <div>
                <label
                  htmlFor="delete-from-date"
                  className="block text-sm font-medium text-zinc-700 mb-2"
                >
                  From
                </label>

                <input
                  id="delete-from-date"
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  className="w-full border border-zinc-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>

              <div>
                <label
                  htmlFor="delete-to-date"
                  className="block text-sm font-medium text-zinc-700 mb-2"
                >
                  To
                </label>

                <input
                  id="delete-to-date"
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  className="w-full border border-zinc-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              </div>
            </div>

            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 px-3 py-3">
              <p className="text-sm text-red-700">
                This action cannot be undone.
              </p>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowDeleteModal(false);
                  setFromDate("");
                  setToDate("");
                }}
                className="px-4 py-2 rounded-lg border border-zinc-300 hover:bg-zinc-50"
              >
                Cancel
              </button>

              <button
                disabled={!fromDate || !toDate}
                onClick={confirmDelete}
                className={`px-4 py-2 rounded-lg text-white transition ${
                  !fromDate || !toDate
                    ? "bg-red-300 cursor-not-allowed"
                    : "bg-red-600 hover:bg-red-700"
                }`}
              >
                Delete Logs
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
