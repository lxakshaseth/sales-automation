"use client";

import { useState } from "react";

import { X } from "lucide-react";

import toast from "react-hot-toast";

import TemplateEditor from "./TemplateEditor";

import { createTemplate } from "@/services/template.service";

type CreateTemplateModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
};

export default function CreateTemplateModal({
  isOpen,
  onClose,
  onSuccess,
}: CreateTemplateModalProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState("email");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [editor, setEditor] = useState<any>(null);

  const VARIABLES = [
    {
      label: "First Name",
      value: "{{firstName}}",
    },
    {
      label: "Last Name",
      value: "{{lastName}}",
    },
    {
      label: "Email",
      value: "{{email}}",
    },
    {
      label: "Company",
      value: "{{company}}",
    },
    {
      label: "Phone",
      value: "{{phone}}",
    },
  ];

  const SUBJECT_VARIABLES = [
    {
      label: "First Name",
      value: "{{firstName}}",
    },
    {
      label: "Last Name",
      value: "{{lastName}}",
    },
  ];

  if (!isOpen) return null;

  async function handleSubmit() {
    try {
      setLoading(true);
      setError("");

      await createTemplate({
        name,
        type,
        subject,
        body,
      });

      toast.success("Template created successfully");

      setName("");
      setType("email");
      setSubject("");
      setBody("");

      onSuccess();
      onClose();
    } catch {
      toast.error("Failed to create template");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl w-full max-w-4xl max-h-[90vh] shadow-2xl border border-[#eef2f7] overflow-hidden flex flex-col">
        {/* HEADER */}
        <div className="flex items-start justify-between px-8 py-6 border-b border-[#eef2f7]">
          <div>
            <h2 className="text-[28px] font-bold text-[#111827]">
              Create Template
            </h2>

            <p className="text-sm text-gray-500 mt-1">
              Create a new email template
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
        <div className="p-8 space-y-5 overflow-y-auto flex-1">
          <div>
            <label className="block text-sm font-semibold text-[#111827] mb-2">
              Template Name
            </label>

            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="welcome_email"
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
                onChange={(e) => setType(e.target.value)}
                className="w-full border border-[#d7dce5] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200"
              >
                <option value="email">Email</option>

                <option value="sms">SMS</option>

                <option value="ai_call">AI Call</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-semibold text-[#111827]">
                  Subject
                </label>
              </div>

              <input
                type="text"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Welcome [firstName] [lastName]!"
                className="w-full border border-[#d7dce5] rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200"
              />

              <div className="flex flex-wrap gap-2 mb-3 pt-2">
                {SUBJECT_VARIABLES.map((variable) => (
                  <button
                    key={variable.value}
                    type="button"
                    onClick={() =>
                      setSubject((prev) => `${prev}${variable.value}`)
                    }
                    className="px-3 py-1.5 text-sm rounded-lg bg-blue-100 text-blue-700 hover:bg-blue-200 transition"
                  >
                    {variable.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <div>
              <div className="flex items-center justify-between mb-2"></div>

              <label className="block text-sm font-semibold text-[#111827] mb-2">
                Body
              </label>
              <div className="flex flex-wrap gap-2 mb-4">
                {VARIABLES.map((variable) => (
                  <button
                    key={variable.value}
                    type="button"
                    onClick={() => {
                      if (!editor) return;

                      editor
                        .chain()
                        .focus()
                        .insertContent(variable.value)
                        .run();
                    }}
                    className="px-3 py-1.5 text-sm rounded-lg bg-violet-100 text-violet-700 hover:bg-violet-200 transition"
                  >
                    {variable.label}
                  </button>
                ))}
              </div>

              <TemplateEditor
                content={body}
                onChange={setBody}
                onEditorReady={setEditor}
              />
            </div>
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
            onClick={handleSubmit}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-violet-600 text-white hover:bg-violet-700 hover:shadow-md transition-all duration-200 disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create Template"}
          </button>
        </div>
      </div>
    </div>
  );
}
