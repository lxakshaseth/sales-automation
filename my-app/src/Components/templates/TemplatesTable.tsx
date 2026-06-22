"use client";

import { Plus, Edit2, Trash2, CheckSquare, X } from "lucide-react";
import CreateTemplateModal from "./CreateTemplateModal";
import TemplatePreviewModal from "./TemplatePreviewModal";
import DeleteTemplateDialog from "./DeleteTemplateDialog";

import { useEffect, useState } from "react";
import { getTemplates, Template, deleteTemplate } from "@/services/template.service";
import toast from "react-hot-toast";

export default function TemplatesTable() {
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isWorkspaceViewOpen, setIsWorkspaceViewOpen] = useState(false);

  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  /* Selection mode states */
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  async function fetchTemplates() {
    try {
      setLoading(true);
      const response = await getTemplates();
      setTemplates(response.data);
      setSelectedIds([]);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === templates.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(templates.map((t) => t._id));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) {
      toast.error("Please select at least one template");
      return;
    }
    
    const confirmDelete = window.confirm(`Are you sure you want to delete ${selectedIds.length} selected template(s)?`);
    if (!confirmDelete) return;

    try {
      setIsBulkDeleting(true);
      await Promise.all(selectedIds.map((id) => deleteTemplate(id)));
      toast.success("Selected templates deleted successfully");
      setIsSelectionMode(false);
      fetchTemplates();
    } catch (err) {
      toast.error("Failed to delete some templates");
    } finally {
      setIsBulkDeleting(false);
    }
  };

  /* Cancel selection mode */
  const handleCancelSelection = () => {
    setIsSelectionMode(false);
    setSelectedIds([]);
  };

  if (isWorkspaceViewOpen) {
    return (
      <CreateTemplateModal
        isOpen={true}
        onClose={() => {
          setIsWorkspaceViewOpen(false);
          setSelectedTemplate(null);
        }}
        onSuccess={fetchTemplates}
        initialData={selectedTemplate}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-[32px] font-bold text-[#111827]">Email Templates</h1>
          <p className="text-gray-500 text-sm mt-0.5">Manage and monitor your email templates efficiently.</p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
          {!isSelectionMode ? (
            <>
              <button
                onClick={() => setIsSelectionMode(true)}
                className="h-11 px-5 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold flex items-center gap-2 transition-all shadow-sm"
              >
                <CheckSquare size={18} />
                Select
              </button>

              <button
                onClick={() => {
                  setSelectedTemplate(null);
                  setIsWorkspaceViewOpen(true);
                }}
                className="h-11 px-5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-semibold flex items-center gap-2 transition-all shadow-sm"
              >
                <Plus size={18} />
                Create Template
              </button>
            </>
          ) : (
            <>
              <button
                onClick={handleCancelSelection}
                className="h-11 px-5 rounded-xl border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold flex items-center gap-2 transition-all shadow-sm"
              >
                <X size={18} />
                Cancel
              </button>

              <button
                onClick={handleBulkDelete}
                disabled={isBulkDeleting || selectedIds.length === 0}
                className="h-11 px-5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold flex items-center gap-2 transition-all shadow-sm disabled:opacity-50"
              >
                <Trash2 size={18} />
                Delete Selected ({selectedIds.length})
              </button>
            </>
          )}
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 w-48 bg-gray-200 rounded-xl" />
            <div className="h-16 bg-gray-100 rounded-xl" />
          </div>
        </div>
      ) : error ? (
        <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-6">
          <p className="text-red-500">{error}</p>
        </div>
      ) : (
        <div className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-gray-100 text-[11px] font-bold text-gray-400 uppercase tracking-wider bg-gray-50/50">
      
                {isSelectionMode && (
                  <th className="px-6 py-4 w-12">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500 accent-violet-600 cursor-pointer"
                      checked={templates.length > 0 && selectedIds.length === templates.length}
                      onChange={toggleSelectAll}
                    />
                  </th>
                )}
                <th className="px-6 py-4">Template Name</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Subject</th>
                <th className="px-6 py-4 text-center w-32">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 text-sm font-semibold text-slate-800">
              {templates.map((template) => (
                <tr key={template._id} className="hover:bg-gray-50/40 transition-colors">
                  {/* Conditionally show row checkbox */}
                  {isSelectionMode && (
                    <td className="px-6 py-5">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500 accent-violet-600 cursor-pointer"
                        checked={selectedIds.includes(template._id)}
                        onChange={() => toggleSelect(template._id)}
                      />
                    </td>
                  )}
                  <td className="px-6 py-5 text-[#111827]">{template.name}</td>
                  <td className="px-6 py-5 text-gray-400 font-normal capitalize">{template.type || "email"}</td>
                  <td className="px-6 py-5 text-gray-500 font-normal truncate max-w-xs">{template.subject}</td>
                  <td className="px-6 py-5">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => {
                          setSelectedTemplate(template);
                          setIsWorkspaceViewOpen(true);
                        }}
                        disabled={isSelectionMode}
                        title="Edit Template"
                        className="p-2 text-gray-500 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition-all disabled:opacity-30 disabled:hover:bg-transparent"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => {
                          setSelectedTemplate(template);
                          setIsDeleteOpen(true);
                        }}
                        disabled={isSelectionMode}
                        title="Delete Template"
                        className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all disabled:opacity-30 disabled:hover:bg-transparent"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between">
        <div className="text-sm font-medium text-violet-600 px-2">
          Total: {templates.length} {isSelectionMode && selectedIds.length > 0 && `(${selectedIds.length} selected)`}
        </div>
      </div>

      <TemplatePreviewModal
        template={selectedTemplate}
        isOpen={isPreviewOpen}
        onClose={() => {
          setIsPreviewOpen(false);
          setSelectedTemplate(null);
        }}
      />

      <DeleteTemplateDialog
        template={selectedTemplate}
        isOpen={isDeleteOpen}
        onClose={() => {
          setIsDeleteOpen(false);
          setSelectedTemplate(null);
        }}
        onSuccess={fetchTemplates}
      />
    </div>
  );
}