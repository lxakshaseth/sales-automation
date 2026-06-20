"use client";

import { Plus, Edit2, Trash2 } from "lucide-react";
import CreateTemplateModal from "./CreateTemplateModal";
import TemplatePreviewModal from "./TemplatePreviewModal";
import DeleteTemplateDialog from "./DeleteTemplateDialog";

import { useEffect, useState } from "react";
import { getTemplates, Template } from "@/services/template.service";

export default function TemplatesTable() {
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [isWorkspaceViewOpen, setIsWorkspaceViewOpen] = useState(false);

  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTemplates();
  }, []);

  async function fetchTemplates() {
    try {
      setLoading(true);
      const response = await getTemplates();
      setTemplates(response.data);
    } catch (error: any) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

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
                <th className="px-6 py-4">Template Name</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Subject</th>
                <th className="px-6 py-4 text-center w-32">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 text-sm font-semibold text-slate-800">
              {templates.map((template) => (
                <tr key={template._id} className="hover:bg-gray-50/40 transition-colors">
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
                        title="Edit Template"
                        className="p-2 text-gray-500 hover:text-violet-600 hover:bg-violet-50 rounded-lg transition-all"
                      >
                        <Edit2 size={16} />
                      </button>
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

      <div className="mt-5 flex items-center justify-between">
        <div className="text-sm font-medium text-violet-600 px-2">
          Total: {templates.length}
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