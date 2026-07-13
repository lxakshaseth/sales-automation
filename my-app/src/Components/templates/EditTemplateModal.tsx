"use client";

import { useEffect, useState } from "react";

import { X } from "lucide-react";

import { Template, updateTemplate } from "@/services/template.service";
import toast from "react-hot-toast";

type TemplateType = Template["type"];

type EditTemplateModalProps = {
  template: Template | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

export default function EditTemplateModal({
  template,
  isOpen,
  onClose,
  onSuccess,
}: EditTemplateModalProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState<TemplateType>("email");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    if (template) {
      setName(template.name);
      setType(template.type);
      setSubject(template.subject);
      setBody(template.body);
    }
  }, [template]);

  if (!isOpen || !template) return null;

  const selectedTemplate = template;

  async function handleUpdate() {
    try {
      setLoading(true);
      setError("");

      await updateTemplate(selectedTemplate._id, {
        name,
        type,
        subject,
        body,
      });

      toast.success("Template updated successfully");

      onSuccess();
      onClose();
    } catch {
      toast.error("Failed to update template");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl w-full max-w-2xl shadow-2xl border border-[#eef2f7] overflow-hidden">
        {/* HEADER */}
        <div className="flex items-start justify-between px-8 py-6 border-b border-[#eef2f7]">
          <div>
            <h2 className="text-[28px] font-bold text-[#111827]">
              Edit Template
            </h2>

            <p className="text-sm text-gray-500 mt-1">
              Update your template details
            </p>
          </div>

          <button
            onClick={onClose}
            className="h-10 w-10 rounded-xl hover:bg-gray-100 flex items-center justify-center transition-all duration-200"
          >
            <X size={20} />
          </button>
        </div>

        {/* BODY */}
        <div className="p-8 space-y-5">
          <div>
            <label className="block text-sm font-semibold text-[#111827] mb-2">
              Template Name
            </label>

            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Template Name"
              className="w-full border border-[#d7dce5] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-[#111827] mb-2">
                Type
              </label>

              <select
                value={type}
                onChange={(e) => setType(e.target.value as TemplateType)}
                className="w-full border border-[#d7dce5] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200"
              >
                <option value="email">Email</option>

                <option value="sms">SMS</option>

                <option value="ai_call">AI Call</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-[#111827] mb-2">
                Subject
              </label>

              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Subject"
                className="w-full border border-[#d7dce5] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-[#111827] mb-2">
              Template Body
            </label>

            <textarea
              rows={8}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full border border-[#d7dce5] rounded-xl px-4 py-3 resize-none outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}
        </div>

        {/* FOOTER */}
        <div className="flex justify-end gap-3 px-8 py-5 border-t border-[#eef2f7] bg-[#fafbfc]">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-5 py-2.5 border border-[#d7dce5] rounded-xl hover:bg-gray-50 transition-all duration-200"
          >
            Cancel
          </button>

          <button
            onClick={handleUpdate}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-violet-600 text-white hover:bg-violet-700 hover:shadow-md transition-all duration-200 disabled:opacity-50"
          >
            {loading ? "Updating..." : "Update Template"}
          </button>
        </div>
      </div>
    </div>
  );
}
