"use client";

import { motion } from "framer-motion";
import { Plus, Search, ChevronLeft, ChevronRight, Eye, ArrowUpDown, Pencil, Trash2, X, Loader2 } from "lucide-react";
import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { getCampaigns, updateCampaign, deleteCampaign as deleteCampaignApi } from "@/services/campaign.service";

type TemplateRef = {
  _id: string;
  name: string;
};

type Campaign = {
  _id: string;
  name: string;
  description?: string;
  status: "draft" | "active";
  emailTemplates?: TemplateRef[];
  smsTemplates?: TemplateRef[];
  createdAt: string;
  updatedAt: string;
};

const STATUS_TABS = ["All", "Draft", "Active"];
const PAGE_SIZE = 8;

const statusColor: Record<string, string> = {
  active: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  draft: "bg-orange-100 text-orange-600 border border-orange-200",
};

function formatDate(dateStr?: string) {
  if (!dateStr) return "-";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return "-";
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function getAssignedTemplateNames(c: Campaign) {
  const names = [
    ...(c.emailTemplates?.map((t) => t.name) || []),
    ...(c.smsTemplates?.map((t) => t.name) || []),
  ];
  return names.length > 0 ? names : null;
}

export default function Campaigns() {
  const router = useRouter();

  useEffect(() => {
    const token = sessionStorage.getItem("token");
    if (!token) {
      router.replace("/sign-in");
    }
  }, []);

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [totalData, setTotalData] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [activeTab, setActiveTab] = useState("All");
  const [page, setPage] = useState(1);

  const [viewCampaign, setViewCampaign] = useState<Campaign | null>(null);

  const [editCampaign, setEditCampaign] = useState<Campaign | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editStatus, setEditStatus] = useState<Campaign["status"]>("draft");
  const [savingEdit, setSavingEdit] = useState(false);

  const [deleteCampaignTarget, setDeleteCampaignTarget] = useState<Campaign | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusParam =
        activeTab === "All" ? undefined : activeTab.toLowerCase();
      const res = await getCampaigns({
        page,
        limit: PAGE_SIZE,
        name: searchTerm || undefined,
        status: statusParam,
      });
      setCampaigns(res.data || []);
      setTotalData(res.totalData || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load campaigns");
      setCampaigns([]);
      setTotalData(0);
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, activeTab]);

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  const totalPages = Math.max(1, Math.ceil(totalData / PAGE_SIZE));

  const handleSaveEdit = async () => {
    if (!editCampaign) return;
    if (!editName.trim()) {
      toast.error("Campaign name is required");
      return;
    }
    try {
      setSavingEdit(true);
      await updateCampaign(editCampaign._id, {
        name: editName,
        description: editDescription,
        status: editStatus,
      });
      toast.success("Campaign updated successfully");
      setEditCampaign(null);
      fetchCampaigns();
    } catch (err: any) {
      toast.error(err.message || "Failed to update campaign");
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteCampaignTarget) return;
    try {
      setDeleting(true);
      await deleteCampaignApi(deleteCampaignTarget._id);
      toast.success("Campaign deleted successfully");
      setDeleteCampaignTarget(null);
      fetchCampaigns();
    } catch (err: any) {
      toast.error(err.message || "Failed to delete campaign");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Table Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="bg-white rounded-2xl border border-zinc-400 mt-5 shadow-sm overflow-hidden"
      >
        {/* Tabs + Create button */}
        <div className="flex items-center justify-between gap-3 px-4 pt-4 border-b border-zinc-100">
          <div className="flex items-center gap-1">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  setPage(1);
                }}
                className={`px-5 py-2 text-sm font-medium rounded-t-xl transition-colors ${
                  activeTab === tab
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-500 hover:text-zinc-700 hover:bg-zinc-50"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          <Link
            href="/Campaign/create"
            className="flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm shadow-violet-600/20 text-sm mb-2 whitespace-nowrap"
          >
            <Plus size={16} />
            Create Campaign
          </Link>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-zinc-100">
          <div className="relative w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-zinc-50 border border-zinc-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all"
            />
          </div>
          <span className="text-sm text-zinc-500 ml-auto">
            {loading ? "Loading..." : `${totalData} campaign${totalData === 1 ? "" : "s"}`}
          </span>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-zinc-50 border-b border-zinc-100">
                {[
                  { label: "Name", sort: false },
                  { label: "Description", sort: false },
                  { label: "Template Assigned", sort: false },
                  { label: "Status", sort: false },
                  { label: "Date", sort: false },
                  { label: "", sort: false },
                ].map((col) => (
                  <th
                    key={col.label}
                    className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide whitespace-nowrap"
                  >
                    <span className="flex items-center gap-1">
                      {col.label}
                      {col.sort && <ArrowUpDown size={11} className="text-zinc-400" />}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-16 text-zinc-400 text-sm">
                    <div className="flex items-center justify-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      Loading campaigns...
                    </div>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={6} className="text-center py-16 text-red-500 text-sm">
                    {error}
                  </td>
                </tr>
              ) : campaigns.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-16 text-zinc-400 text-sm">
                    No campaigns found
                  </td>
                </tr>
              ) : (
                campaigns.map((c, i) => {
                  const assignedTemplates = getAssignedTemplateNames(c);
                  return (
                    <tr
                      key={c._id}
                      className={`border-b border-zinc-100 hover:bg-zinc-50 transition-colors ${
                        i % 2 === 0 ? "" : "bg-zinc-50/30"
                      }`}
                    >
                      {/* Name */}
                      <td className="px-4 py-3">
                        <span className="text-sm font-medium text-zinc-800">{c.name}</span>
                      </td>
                      {/* Description */}
                      <td className="px-4 py-3 max-w-xs">
                        <span className="text-sm text-zinc-600 line-clamp-1">
                          {c.description || "-"}
                        </span>
                      </td>
                      {/* Template Assigned */}
                      <td className="px-4 py-3">
                        {assignedTemplates ? (
                          <div className="flex flex-wrap gap-1">
                            {assignedTemplates.map((name, idx) => (
                              <span
                                key={idx}
                                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-zinc-100 text-zinc-600 border border-zinc-200"
                              >
                                {name}
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-sm text-zinc-400">-</span>
                        )}
                      </td>
                      {/* Status */}
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${
                            statusColor[c.status] ?? "bg-zinc-100 text-zinc-600"
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      {/* Date */}
                      <td className="px-4 py-3 text-sm text-zinc-700">
                        {formatDate(c.createdAt)}
                      </td>
                      {/* Actions */}
                        <td className="px-3 py-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => {
                                setEditCampaign(c);
                                setEditName(c.name);
                                setEditDescription(c.description || "");
                                setEditStatus(c.status);
                              }}
                              title="Edit"
                              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
                            >
                              <Pencil size={16} />
                            </button>
                            <button
                              onClick={() => setDeleteCampaignTarget(c)}
                              title="Delete"
                              className="p-1.5 rounded-lg text-zinc-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-zinc-100">
          <p className="text-xs text-zinc-400">Showing {campaigns.length} of {totalData} campaigns</p>
          {totalPages > 1 && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft size={16} />
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                <button
                  key={n}
                  onClick={() => setPage(n)}
                  className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                    page === n ? "bg-zinc-900 text-white" : "text-zinc-500 hover:bg-zinc-100"
                  }`}
                >
                  {n}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
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
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Description</label>
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  rows={3}
                  className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all resize-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-700 mb-1.5">Status</label>
                <select
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value as Campaign["status"])}
                  className="w-full border border-zinc-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all bg-white capitalize"
                >
                  {["draft", "active"].map((s) => (
                    <option key={s} value={s} className="capitalize">
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-zinc-100">
              <button
                onClick={() => setEditCampaign(null)}
                disabled={savingEdit}
                className="px-4 py-2 text-sm border border-zinc-200 rounded-xl hover:bg-zinc-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={savingEdit}
                className="px-4 py-2 text-sm bg-violet-600 hover:bg-violet-700 text-white rounded-xl transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {savingEdit && <Loader2 size={14} className="animate-spin" />}
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* View Modal */}
      {viewCampaign && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl border border-zinc-200">
            <div className="flex items-center justify-between px-6 py-5 border-b border-zinc-100">
              <h2 className="text-lg font-bold text-zinc-900">Campaign Details</h2>
              <button onClick={() => setViewCampaign(null)} className="p-1.5 rounded-lg hover:bg-zinc-100 transition-colors">
                <X size={18} className="text-zinc-500" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-1">Name</p>
                <p className="text-sm text-zinc-800">{viewCampaign.name}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-1">Description</p>
                <p className="text-sm text-zinc-700">{viewCampaign.description || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-1">Template Assigned</p>
                {getAssignedTemplateNames(viewCampaign) ? (
                  <div className="flex flex-wrap gap-1">
                    {getAssignedTemplateNames(viewCampaign)!.map((name, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-zinc-100 text-zinc-600 border border-zinc-200"
                      >
                        {name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-zinc-400">-</p>
                )}
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-1">Status</p>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize ${
                    statusColor[viewCampaign.status] ?? "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {viewCampaign.status}
                </span>
              </div>
              <div>
                <p className="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-1">Date</p>
                <p className="text-sm text-zinc-700">{formatDate(viewCampaign.createdAt)}</p>
              </div>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-zinc-100">
              <button
                onClick={() => setViewCampaign(null)}
                className="px-4 py-2 text-sm border border-zinc-200 rounded-xl hover:bg-zinc-50 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirm Dialog */}
      {deleteCampaignTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl w-full max-w-sm shadow-2xl border border-zinc-200">
            <div className="p-6">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mb-4">
                <Trash2 size={22} className="text-red-500" />
              </div>
              <h2 className="text-lg font-bold text-zinc-900 mb-1">Delete Campaign?</h2>
              <p className="text-sm text-zinc-500">
                <span className="font-semibold text-zinc-700">&ldquo;{deleteCampaignTarget.name}&rdquo;</span> cannot be undone once deleted.
              </p>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t border-zinc-100">
              <button
                onClick={() => setDeleteCampaignTarget(null)}
                disabled={deleting}
                className="px-4 py-2 text-sm border border-zinc-200 rounded-xl hover:bg-zinc-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-xl transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {deleting && <Loader2 size={14} className="animate-spin" />}
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}