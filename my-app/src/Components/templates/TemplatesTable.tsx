"use client";

import { Plus } from "lucide-react";
import CreateTemplateModal from "./CreateTemplateModal";
import TemplateActionMenu from "./TemplateActionMenu";
import TemplatePreviewModal from "./TemplatePreviewModal";
import EditTemplateModal from "./EditTemplateModal";
import DeleteTemplateDialog from "./DeleteTemplateDialog";

import { useEffect, useState } from "react";

import { getTemplates, Template } from "@/services/template.service";

export default function TemplatesTable() {
  const [isEditOpen, setIsEditOpen] = useState(false);

  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(
    null,
  );

  const [isPreviewOpen, setIsPreviewOpen] = useState(false);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

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

  if (loading) {
    return (
      <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 bg-gray-200 rounded-xl" />

          <div className="h-16 bg-gray-100 rounded-xl" />

          <div className="h-16 bg-gray-100 rounded-xl" />

          <div className="h-16 bg-gray-100 rounded-xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-6">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-6">
      {/* HEADER */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-[26px] font-bold text-[#111827]">Templates</h2>

          <p className="text-gray-500 text-sm mt-1">
            Manage your email templates
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="h-11 px-5 rounded-xl border border-violet-200 text-violet-600 bg-violet-50 hover:bg-violet-100 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex items-center gap-2 font-medium"
        >
          <Plus size={18} />
          Create Template
        </button>
      </div>

      {/* EMPTY STATE */}
      {templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-[280px] border border-dashed border-[#d7dce5] rounded-2xl bg-gradient-to-b from-white to-[#fafbff]">
          <div className="w-16 h-16 rounded-2xl bg-violet-100 flex items-center justify-center mb-4">
            <Plus size={28} className="text-violet-600" />
          </div>

          <h3 className="text-lg font-semibold text-[#111827]">
            No Templates Yet
          </h3>

          <p className="text-gray-500 mt-1">Create your first email template</p>
        </div>
      ) : (
        <div className="overflow-visible rounded-2xl border border-[#e9edf5] shadow-sm">
          <table className="w-full">
            <thead>
              <tr className="bg-gradient-to-r from-[#f8fafc] to-[#fdfdff] border-b border-[#e9edf5]">
                <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                  Name
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                  Type
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                  Subject
                </th>

                <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                  Created
                </th>

                <th className="px-6 py-4 text-center text-xs font-semibold text-[#64748b] uppercase">
                  Actions
                </th>
              </tr>
            </thead>

            <tbody>
              {templates.map((template) => (
                <tr
                  key={template._id}
                  className="border-b border-[#edf1f7] hover:bg-[#fafbfc] hover:shadow-sm transition-all duration-200"
                >
                  <td className="px-6 py-5 font-semibold text-[#111827]">
                    {template.name}
                  </td>

                  <td className="px-6 py-5">
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-100 text-violet-700 border border-violet-200">
                      {template.type}
                    </span>
                  </td>

                  <td className="px-6 py-5 text-gray-600 max-w-[300px] truncate">
                    {template.subject}
                  </td>

                  <td className="px-6 py-5 text-gray-600">
                    {new Date(template.createdAt).toLocaleDateString()}
                  </td>

                  <td className="px-6 py-5 text-center relative overflow-visible">
                    <TemplateActionMenu
                      onView={() => {
                        setSelectedTemplate(template);
                        setIsPreviewOpen(true);
                      }}
                      onEdit={() => {
                        setSelectedTemplate(template);
                        setIsEditOpen(true);
                      }}
                      onDelete={() => {
                        setSelectedTemplate(template);
                        setIsDeleteOpen(true);
                      }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between">
        <div className="text-sm font-medium text-violet-600">
          Total: {templates.length}
        </div>
      </div>
      <CreateTemplateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={fetchTemplates}
      />

      <TemplatePreviewModal
        template={selectedTemplate}
        isOpen={isPreviewOpen}
        onClose={() => {
          setIsPreviewOpen(false);
          setSelectedTemplate(null);
        }}
      />

      <EditTemplateModal
        template={selectedTemplate}
        isOpen={isEditOpen}
        onClose={() => {
          setIsEditOpen(false);
          setSelectedTemplate(null);
        }}
        onSuccess={fetchTemplates}
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
