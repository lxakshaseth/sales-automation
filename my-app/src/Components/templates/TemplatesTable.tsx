"use client";

import { Plus, Edit2, Trash2, Eye, Search } from "lucide-react";
import CreateTemplateModal from "./CreateTemplateModal";
import TemplatePreviewModal from "./TemplatePreviewModal";
import DeleteTemplateDialog from "./DeleteTemplateDialog";

import { useEffect, useMemo, useState } from "react";
import {
  getTemplates,
  Template,
  deleteTemplate,
} from "@/services/template.service";
import toast from "react-hot-toast";
import Pagination from "@/Components/ui/Pagination";

const DEFAULT_PAGE_SIZE = 10;

export default function TemplatesTable() {
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null,
  );
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editData, setEditData] = useState<Template | null>(null);

  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);

  /* Selection states */
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);

  /* Search */
  const [templateSearch, setTemplateSearch] = useState("");

  useEffect(() => {
    fetchTemplates();
  }, []);

  async function fetchTemplates() {
    try {
      setLoading(true);
      const response = await getTemplates();
      setTemplates(response.data);
      setSelectedIds([]);
      setCurrentPage(1);
    } catch {
      setError("Failed to fetch templates");
      toast.error("Failed to load templates");
    } finally {
      setLoading(false);
    }
  }

  const filteredTemplates = useMemo(() => {
    return templates.filter(
      (t) =>
        t.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
        t.subject?.toLowerCase().includes(templateSearch.toLowerCase()),
    );
  }, [templates, templateSearch]);

  const totalPages = Math.max(1, Math.ceil(filteredTemplates.length / pageSize));
  const activePage = Math.min(currentPage, totalPages);
  const paginatedTemplates = useMemo(() => {
    const start = (activePage - 1) * pageSize;
    return filteredTemplates.slice(start, start + pageSize);
  }, [activePage, pageSize, filteredTemplates]);

  const handleSelectAll = () => {
    const visibleIds = paginatedTemplates.map((template) => template._id);
    const allVisibleSelected = visibleIds.every((id) =>
      selectedIds.includes(id),
    );

    if (allVisibleSelected) {
      setSelectedIds((prev) => prev.filter((id) => !visibleIds.includes(id)));
    } else {
      setSelectedIds((prev) => Array.from(new Set([...prev, ...visibleIds])));
    }
  };

  const handleSelectOne = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter((item) => item !== id));
    } else {
      setSelectedIds([...selectedIds, id]);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    try {
      setIsBulkDeleting(true);
      for (const id of selectedIds) {
        await deleteTemplate(id);
      }
      toast.success("Selected templates deleted successfully");
      fetchTemplates();
    } catch {
      toast.error("Failed to delete some templates");
    } finally {
      setIsBulkDeleting(false);
    }
  };

  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1);
    setSelectedIds([]);
  };

  return (
    <div className="bg-white rounded-3xl border border-[#eef2f7] p-6 shadow-sm">
      {/* TOOLBAR */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search templates..."
            value={templateSearch}
            onChange={(e) => {
              setTemplateSearch(e.target.value);
              setCurrentPage(1);
            }}
            className="w-full pl-9 pr-4 py-2.5 border border-zinc-200 rounded-xl text-sm"
          />
        </div>

        <div className="flex items-center gap-2">
          {selectedIds.length > 0 && (
            <button
              onClick={handleBulkDelete}
              disabled={isBulkDeleting}
              className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-2 disabled:opacity-50"
            >
              <Trash2 size={16} />
              Delete Selected ({selectedIds.length})
            </button>
          )}

          <button
            onClick={() => {
              setEditData(null);
              setIsCreateOpen(true);
            }}
            className="w-full sm:w-auto px-5 py-2.5 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-sm"
          >
            <Plus size={16} />
            Create Template
          </button>
        </div>
      </div>

      {/* TABLE */}
      {loading ? (
        <div className="py-20 text-center text-gray-500 font-medium">
          Loading templates...
        </div>
      ) : error ? (
        <div className="py-20 text-center text-red-500 font-medium">
          {error}
        </div>
      ) : templates.length === 0 ? (
        <div className="py-20 text-center text-gray-400 font-medium">
          No templates found. Create one to get started!
        </div>
      ) : filteredTemplates.length === 0 ? (
        <div className="py-20 text-center text-gray-400 font-medium">
          No templates match your search.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-[#eef2f7]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#fafbfc] border-b border-[#eef2f7]">
                <th className="p-4 w-12 text-center">
                  <input
                    type="checkbox"
                    checked={
                      paginatedTemplates.length > 0 &&
                      paginatedTemplates.every((template) =>
                        selectedIds.includes(template._id),
                      )
                    }
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-violet-600 focus:ring-violet-500 h-4 w-4"
                  />
                </th>
                <th className="p-4 text-xs uppercase tracking-wider text-[#6b7280] font-semibold">
                  Name
                </th>
                <th className="p-4 text-xs uppercase tracking-wider text-[#6b7280] font-semibold">
                  Type
                </th>
                <th className="p-4 text-xs uppercase tracking-wider text-[#6b7280] font-semibold">
                  Subject
                </th>
                <th className="p-4 text-xs uppercase tracking-wider text-[#6b7280] font-semibold text-right">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#eef2f7]">
              {paginatedTemplates.map((template) => (
                <tr
                  key={template._id}
                  className="hover:bg-gray-50 transition-colors"
                >
                  <td className="p-4 text-center">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(template._id)}
                      onChange={() => handleSelectOne(template._id)}
                      className="rounded border-gray-300 text-violet-600 focus:ring-violet-500 h-4 w-4"
                    />
                  </td>
                  <td className="p-4 font-semibold text-[#111827]">
                    {template.name}
                  </td>
                  <td className="p-4">
                    <span className="inline-flex px-2.5 py-1 text-xs font-semibold rounded-full bg-violet-50 text-violet-700 capitalize">
                      {template.type}
                    </span>
                  </td>
                  <td className="p-4 text-gray-500 max-w-xs truncate">
                    {template.subject || "—"}
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {/* VIEW BUTTON */}
                      <button
                        onClick={() => {
                          setSelectedTemplate(template);
                          setIsPreviewOpen(true);
                        }}
                        title="View Template"
                        className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                      >
                        <Eye size={16} />
                      </button>

                      {/* EDIT BUTTON */}
                      <button
                        onClick={() => {
                          setEditData(template);
                          setIsCreateOpen(true);
                        }}
                        title="Edit Template"
                        className="p-2 text-gray-500 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition-all"
                      >
                        <Edit2 size={16} />
                      </button>

                      {/* DELETE BUTTON */}
                      <button
                        onClick={() => {
                          setSelectedTemplate(template);
                          setIsDeleteOpen(true);
                        }}
                        title="Delete Template"
                        className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
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

      <div className="mt-5">
        {selectedIds.length > 0 && (
          <div className="mb-3 px-2 text-sm font-medium text-violet-600">
            {selectedIds.length} selected
          </div>
        )}
        <Pagination
          currentPage={activePage}
          totalPages={totalPages}
          totalItems={filteredTemplates.length}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
          onPageSizeChange={handlePageSizeChange}
          itemLabel="templates"
        />
      </div>

      {/* MODALS */}
      <CreateTemplateModal
        isOpen={isCreateOpen}
        onClose={() => {
          setIsCreateOpen(false);
          setEditData(null);
        }}
        onSuccess={fetchTemplates}
        initialData={editData}
      />

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