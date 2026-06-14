"use client";

import { X, Mail, FileText, Calendar } from "lucide-react";

import { Template } from "@/services/template.service";

type TemplatePreviewModalProps = {
  template: Template | null;
  isOpen: boolean;
  onClose: () => void;
};

export default function TemplatePreviewModal({
  template,
  isOpen,
  onClose,
}: TemplatePreviewModalProps) {
  if (!isOpen || !template) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl w-full max-w-4xl shadow-2xl overflow-hidden">
        {/* HEADER */}
        <div className="flex items-start justify-between px-8 py-6 border-b border-[#eef2f7]">
          <div>
            <h2 className="text-3xl font-bold text-[#111827]">
              Template Preview
            </h2>

            <p className="text-gray-500 mt-1">
              Preview how recipients will receive this email
            </p>
          </div>

          <button
            onClick={onClose}
            className="h-10 w-10 rounded-xl hover:bg-gray-100 flex items-center justify-center transition-all"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-8 overflow-y-auto max-h-[85vh]">
          {/* TEMPLATE INFO */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="border border-[#e7ebf3] rounded-2xl p-5 bg-[#fafcff]">
              <div className="flex items-center gap-2 mb-3">
                <FileText size={18} className="text-violet-600" />

                <span className="text-sm text-gray-500">Template Name</span>
              </div>

              <p className="font-semibold text-[#111827]">{template.name}</p>
            </div>

            <div className="border border-[#e7ebf3] rounded-2xl p-5 bg-[#fafcff]">
              <div className="flex items-center gap-2 mb-3">
                <Mail size={18} className="text-violet-600" />

                <span className="text-sm text-gray-500">Type</span>
              </div>

              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-100 text-violet-700 border border-violet-200">
                {template.type}
              </span>
            </div>

            <div className="border border-[#e7ebf3] rounded-2xl p-5 bg-[#fafcff]">
              <div className="flex items-center gap-2 mb-3">
                <Calendar size={18} className="text-violet-600" />

                <span className="text-sm text-gray-500">Created</span>
              </div>

              <p className="font-medium text-[#111827]">
                {new Date(template.createdAt).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* EMAIL PREVIEW */}
          <div className="rounded-3xl border border-[#e7ebf3] overflow-hidden shadow-sm bg-white">
            {/* EMAIL HEADER */}
            <div className="px-8 py-6 border-b border-[#eef2f7] bg-[#fafbfc]">
              <div className="flex items-start gap-4">
                <div className="h-12 w-12 rounded-full bg-violet-100 flex items-center justify-center flex-shrink-0">
                  <Mail size={20} className="text-violet-600" />
                </div>

                <div className="flex-1">
                  <h3 className="text-[22px] font-bold text-[#111827] mb-4">
                    {template.subject}
                  </h3>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-semibold text-[#111827]">
                        Sales Automation
                      </p>

                      <p className="text-sm text-gray-500">
                        noreply@company.com
                      </p>
                    </div>

                    <span className="text-sm text-gray-400">just now</span>
                  </div>
                </div>
              </div>
            </div>

            {/* EMAIL BODY */}
            <div className="p-8 bg-white">
              <div
                className="max-w-none"
                dangerouslySetInnerHTML={{
                  __html: template.body,
                }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
