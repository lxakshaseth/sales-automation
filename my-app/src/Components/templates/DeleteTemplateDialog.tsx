"use client";

import { useState } from "react";

import { AlertTriangle, X } from "lucide-react";

import { Template, deleteTemplate } from "@/services/template.service";
import toast from "react-hot-toast";

type DeleteTemplateDialogProps = {
  template: Template | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

export default function DeleteTemplateDialog({
  template,
  isOpen,
  onClose,
  onSuccess,
}: DeleteTemplateDialogProps) {
  const [loading, setLoading] = useState(false);

  if (!isOpen || !template) return null;

  const templateId = template._id;
  const templateName = template.name;

  async function handleDelete() {
    try {
      setLoading(true);

      await deleteTemplate(templateId);

      toast.success("Template deleted successfully");

      onSuccess();
      onClose();
    } catch {
      toast.error("Failed to delete template");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl w-full max-w-md shadow-2xl border border-[#eef2f7] overflow-hidden">
        {/* HEADER */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-[#eef2f7]">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-2xl bg-red-100 flex items-center justify-center">
              <AlertTriangle size={22} className="text-red-600" />
            </div>

            <div>
              <h2 className="text-xl font-bold text-[#111827]">
                Delete Template
              </h2>

              <p className="text-sm text-gray-500 mt-1">
                This action cannot be undone
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            disabled={loading}
            className="h-10 w-10 rounded-xl hover:bg-gray-100 flex items-center justify-center transition-all duration-200"
          >
            <X size={18} />
          </button>
        </div>

        {/* BODY */}
        <div className="px-6 py-6">
          <p className="text-gray-600">
            Are you sure you want to delete this template?
          </p>

          <div className="mt-4 p-4 rounded-2xl border border-red-200 bg-red-50">
            <p className="text-xs uppercase tracking-wide text-red-500 font-semibold mb-1">
              Template
            </p>

            <p className="font-semibold text-[#111827] break-all">
              {templateName}
            </p>
          </div>
        </div>

        {/* FOOTER */}
        <div className="flex justify-end gap-3 px-6 py-5 border-t border-[#eef2f7] bg-[#fafbfc]">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-5 py-2.5 border border-[#d7dce5] rounded-xl hover:bg-gray-50 transition-all duration-200"
          >
            Cancel
          </button>

          <button
            onClick={handleDelete}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-red-600 text-white hover:bg-red-700 hover:shadow-md transition-all duration-200 disabled:opacity-50"
          >
            {loading ? "Deleting..." : "Delete Template"}
          </button>
        </div>
      </div>
    </div>
  );
}