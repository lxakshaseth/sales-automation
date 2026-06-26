"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowLeft, Save, Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import TemplateEditor from "./TemplateEditor";
import { createTemplate, updateTemplate } from "@/services/template.service";

type CustomVar = {
  id: string;
  label: string;
  value: string;
};

type CreateTemplateModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  initialData?: any;
};

export default function CreateTemplateModal({
  isOpen,
  onClose,
  onSuccess,
  initialData,
}: CreateTemplateModalProps) {
  const [name, setName] = useState("");
  const [type, setType] = useState<"email" | "sms" | "ai_call">("email");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [editor, setEditor] = useState<any>(null);
  
  const [subjectVars, setSubjectVars] = useState<CustomVar[]>([]);
  const [bodyVars, setBodyVars] = useState<CustomVar[]>([]);
  
  const [previewFirstName, setPreviewFirstName] = useState("Arpita");
  const [previewLastName, setPreviewLastName] = useState("Kulkarni");

  const subjectInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialData && isOpen) {
      setName(initialData.name || "");
      setType(initialData.type || "email");
      setSubject(initialData.subject || "");
      setBody(initialData.body || "");
    } else if (!isOpen) {
      setName("");
      setType("email");
      setSubject("");
      setBody("");
      setSubjectVars([]);
      setBodyVars([]);
    }
  }, [initialData, isOpen]);

  useEffect(() => {
    if (isOpen && editor && !editor.isDestroyed) {
      if (initialData?.body) {
        editor.commands?.setContent(initialData.body);
      } else if (!initialData) {
        editor.commands?.setContent("");
      }
    }
  }, [editor, initialData, isOpen]);

  if (!isOpen) return null;

  const addSubjectVar = () => {
    setSubjectVars([...subjectVars, { id: Date.now().toString(), label: "", value: "" }]);
  };

  const addBodyVar = () => {
    setBodyVars([...bodyVars, { id: Date.now().toString(), label: "", value: "" }]);
  };

  const injectIntoSubject = (tokenLabel: string) => {
    if (!tokenLabel.trim()) return;
    const formatToken = `{{${tokenLabel.trim()}}}`;
    const start = subjectInputRef.current?.selectionStart || 0;
    const end = subjectInputRef.current?.selectionEnd || 0;
    const nextSubject = subject.substring(0, start) + formatToken + subject.substring(end);
    setSubject(nextSubject);
    
    setTimeout(() => {
      if (subjectInputRef.current) {
        subjectInputRef.current.focus();
        subjectInputRef.current.setSelectionRange(start + formatToken.length, start + formatToken.length);
      }
    }, 10);
  };

  const injectIntoBody = (tokenLabel: string) => {
    if (!tokenLabel.trim()) return;
    const formatToken = `{{${tokenLabel.trim()}}}`;
    if (editor && !editor.isDestroyed) {
      editor.chain().focus().insertContent(formatToken).run();
    } else {
      toast.error("Please click inside the Body Editor first");
    }
  };

  const renderLivePreview = (text: string) => {
    let updatedText = text;
    updatedText = updatedText.replace(/{{\s*first_name\s*}}/g, previewFirstName);
    updatedText = updatedText.replace(/{{\s*last_name\s*}}/g, previewLastName);
    updatedText = updatedText.replace(/{{\s*company\s*}}/g, "Indux Technology");
    updatedText = updatedText.replace(/{{\s*email\s*}}/g, "user@example.com");
    
    subjectVars.forEach((v) => {
      if (v.label.trim()) {
        const regex = new RegExp(`{{\\s*${v.label.trim()}\\s*}}`, "g");
        updatedText = updatedText.replace(regex, v.value || `[${v.label.trim()}]`);
      }
    });

    bodyVars.forEach((v) => {
      if (v.label.trim()) {
        const regex = new RegExp(`{{\\s*${v.label.trim()}\\s*}}`, "g");
        updatedText = updatedText.replace(regex, v.value || `[${v.label.trim()}]`);
      }
    });

    return updatedText;
  };

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error("Template Name is required");
      return;
    }

    if (!subject.trim()) {
      toast.error("Subject Line is required");
      return;
    }

    if (!body.trim() || body === "<p></p>") {
      toast.error("Body Content is required");
      return;
    }

    try {
      setLoading(true);
      
      const payload = { name, type, subject, body };

      if (initialData?._id) {
        await updateTemplate(initialData._id, payload);
        toast.success("Template updated successfully");
      } else {
        await createTemplate(payload);
        toast.success("Template created successfully");
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      const msg = err?.response?.data?.message || "";
      
      if (msg.toLowerCase().includes("duplicate") || msg.toLowerCase().includes("exists") || err?.response?.status === 409) {
        toast.error("Template name already exists");
      } else {
        toast.error(msg || "Failed to save template");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-gray-900/50 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-6xl h-[85vh] max-h-[90vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden border border-gray-100 animate-in fade-in zoom-in-95 duration-200">
        {/* HEADER */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-white sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-xl text-gray-500 transition-colors border border-transparent hover:border-gray-200"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {initialData ? "Edit Template" : "Create New Template"}
              </h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Design and personalize your communication template
              </p>
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={loading}
            className="px-5 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition-all duration-200 flex items-center gap-2 shadow-sm border border-violet-700"
          >
            <Save size={16} />
            {loading ? "Saving..." : initialData ? "Update Template" : "Save Template"}
          </button>
        </div>

        {/* CONTENT SPLIT SCREEN */}
        <div className="flex-1 flex overflow-hidden bg-gray-50">
          {/* LEFT: FORM EDITOR */}
          <div className="w-7/12 bg-white border-r border-gray-100 flex flex-col overflow-y-auto p-6 space-y-6">
            
            {/* Template Name */}
            <div>
              <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                Template Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g., Welcome Onboarding Email"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-50/50 transition-all font-medium text-gray-900 shadow-sm"
              />
            </div>

            {/* SUBJECT LINE SECTION */}
            <div className="space-y-3 border border-gray-100 p-4 rounded-xl bg-gray-50/30">
              <div className="flex justify-between items-center">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Subject Line <span className="text-red-500">*</span>
                </label>
                <button
                  type="button"
                  onClick={addSubjectVar}
                  className="text-[11px] font-bold text-violet-600 hover:text-violet-700 flex items-center gap-1 bg-violet-50 px-2 py-1 rounded"
                >
                  <Plus size={12} /> Add Subject Var
                </button>
              </div>

              {/* Badges bar */}
              <div className="flex flex-wrap gap-1.5 items-center bg-white p-2 rounded-lg border border-gray-100">
                <span className="text-[10px] text-gray-400 font-bold mr-1">Inject:</span>
                <button
                  type="button"
                  onClick={() => injectIntoSubject("first_name")}
                  className="px-1.5 py-0.5 bg-gray-100 hover:bg-violet-50 border border-gray-200 text-gray-700 text-[10px] font-bold rounded"
                >
                  {"{first_name}"}
                </button>
                <button
                  type="button"
                  onClick={() => injectIntoSubject("last_name")}
                  className="px-1.5 py-0.5 bg-gray-100 hover:bg-violet-50 border border-gray-200 text-gray-700 text-[10px] font-bold rounded"
                >
                  {"{last_name}"}
                </button>
                {subjectVars.map((v) => (
                  v.label.trim() && (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => injectIntoSubject(v.label)}
                      className="px-1.5 py-0.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 text-[10px] font-bold rounded"
                    >
                      {"{"}{v.label}{"}"}
                    </button>
                  )
                ))}
              </div>

              {/* Dynamic Key-Value Inputs */}
              {subjectVars.length > 0 && (
                <div className="space-y-1.5">
                  {subjectVars.map((v) => (
                    <div key={v.id} className="flex items-center gap-2 bg-white p-1.5 border border-gray-200 rounded-lg shadow-sm">
                      <input
                        type="text"
                        placeholder="Variable name"
                        value={v.label}
                        onChange={(e) => setSubjectVars(subjectVars.map((item) => item.id === v.id ? { ...item, label: e.target.value.replace(/[^a-zA-Z0-9_]/g, "") } : item))}
                        className="w-1/2 border border-gray-200 rounded px-2 py-1 text-[11px] outline-none font-semibold text-gray-800"
                      />
                      <input
                        type="text"
                        placeholder="Placeholder value"
                        value={v.value}
                        onChange={(e) => setSubjectVars(subjectVars.map((item) => item.id === v.id ? { ...item, value: e.target.value } : item))}
                        className="w-1/2 border border-gray-200 rounded px-2 py-1 text-[11px] outline-none text-gray-600"
                      />
                      <button
                        type="button"
                        onClick={() => setSubjectVars(subjectVars.filter((item) => item.id !== v.id))}
                        className="text-gray-400 hover:text-red-500 p-1"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <input
                ref={subjectInputRef}
                type="text"
                placeholder="Enter subject line..."
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-50/50 transition-all font-medium text-gray-900 shadow-sm bg-white"
              />
            </div>

            {/* BODY CONTENT SECTION */}
            <div className="flex-1 flex flex-col min-h-[320px] space-y-3 border border-gray-100 p-4 rounded-xl bg-gray-50/30">
              <div className="flex justify-between items-center">
                <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider">
                  Body Content <span className="text-red-500">*</span>
                </label>
                <button
                  type="button"
                  onClick={addBodyVar}
                  className="text-[11px] font-bold text-violet-600 hover:text-violet-700 flex items-center gap-1 bg-violet-50 px-2 py-1 rounded"
                >
                  <Plus size={12} /> Add Body Var
                </button>
              </div>

              {/* Badges bar */}
              <div className="flex flex-wrap gap-1.5 items-center bg-white p-2 rounded-lg border border-gray-100">
                <span className="text-[10px] text-gray-400 font-bold mr-1">Inject:</span>
                <button
                  type="button"
                  onClick={() => injectIntoBody("first_name")}
                  className="px-1.5 py-0.5 bg-gray-100 hover:bg-violet-50 border border-gray-200 text-gray-700 text-[10px] font-bold rounded"
                >
                  {"{first_name}"}
                </button>
                <button
                  type="button"
                  onClick={() => injectIntoBody("last_name")}
                  className="px-1.5 py-0.5 bg-gray-100 hover:bg-violet-50 border border-gray-200 text-gray-700 text-[10px] font-bold rounded"
                >
                  {"{last_name}"}
                </button>
                <button
                  type="button"
                  onClick={() => injectIntoBody("company")}
                  className="px-1.5 py-0.5 bg-gray-100 hover:bg-violet-50 border border-gray-200 text-gray-700 text-[10px] font-bold rounded"
                >
                  {"{company}"}
                </button>
                <button
                  type="button"
                  onClick={() => injectIntoBody("email")}
                  className="px-1.5 py-0.5 bg-gray-100 hover:bg-violet-50 border border-gray-200 text-gray-700 text-[10px] font-bold rounded"
                >
                  {"{email}"}
                </button>
                {bodyVars.map((v) => (
                  v.label.trim() && (
                    <button
                      key={v.id}
                      type="button"
                      onClick={() => injectIntoBody(v.label)}
                      className="px-1.5 py-0.5 bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 text-[10px] font-bold rounded"
                    >
                      {"{"}{v.label}{"}"}
                    </button>
                  )
                ))}
              </div>

              {/* Dynamic Key-Value Inputs */}
              {bodyVars.length > 0 && (
                <div className="space-y-1.5">
                  {bodyVars.map((v) => (
                    <div key={v.id} className="flex items-center gap-2 bg-white p-1.5 border border-gray-200 rounded-lg shadow-sm">
                      <input
                        type="text"
                        placeholder="Variable name"
                        value={v.label}
                        onChange={(e) => setBodyVars(bodyVars.map((item) => item.id === v.id ? { ...item, label: e.target.value.replace(/[^a-zA-Z0-9_]/g, "") } : item))}
                        className="w-1/2 border border-gray-200 rounded px-2 py-1 text-[11px] outline-none font-semibold text-gray-800"
                      />
                      <input
                        type="text"
                        placeholder="Placeholder value"
                        value={v.value}
                        onChange={(e) => setBodyVars(bodyVars.map((item) => item.id === v.id ? { ...item, value: e.target.value } : item))}
                        className="w-1/2 border border-gray-200 rounded px-2 py-1 text-[11px] outline-none text-gray-600"
                      />
                      <button
                        type="button"
                        onClick={() => setBodyVars(bodyVars.filter((item) => item.id !== v.id))}
                        className="text-gray-400 hover:text-red-500 p-1"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex-1 border border-gray-200 rounded-xl overflow-hidden focus-within:border-violet-500 focus-within:ring-2 focus-within:ring-violet-50/50 transition-all bg-white flex flex-col shadow-sm">
                <TemplateEditor
                  content={body}
                  onChange={(html) => setBody(html)}
                  onEditorReady={(inst) => setEditor(inst)}
                />
              </div>
            </div>
          </div>

          {/* RIGHT: LIVE PREVIEW & CONFIGURATION */}
          <div className="w-5/12 flex flex-col p-6 overflow-y-auto bg-gray-50/50 space-y-4">
            <div className="bg-white p-4 rounded-2xl border border-gray-200 shadow-sm space-y-3">
              <div>
                <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Configure Variable Values</h4>
                <p className="text-[10px] text-gray-400">Fill standard variables here to test the live preview compiler</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500 font-mono">{"{{first_name}}"}</label>
                  <input
                    type="text"
                    value={previewFirstName}
                    onChange={(e) => setPreviewFirstName(e.target.value)}
                    className="w-full text-xs border border-gray-200 rounded-lg px-2 py-1.5 outline-none focus:border-violet-500 bg-gray-50/50"
                    placeholder="e.g. Arpita"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500 font-mono">{"{{last_name}}"}</label>
                  <input
                    type="text"
                    value={previewLastName}
                    onChange={(e) => setPreviewLastName(e.target.value)}
                    className="w-full text-xs border border-gray-200 rounded-lg px-2 py-1.5 outline-none focus:border-violet-500 bg-gray-50/50"
                    placeholder="e.g. Kulkarni"
                  />
                </div>
              </div>
            </div>

            <div className="flex-1 flex flex-col">
              <div className="mb-2">
                <h3 className="text-xs font-bold text-gray-700 uppercase tracking-wider">Live System Preview</h3>
                <p className="text-[11px] text-gray-400 mt-0.5">Real-time compilation of system variables</p>
              </div>

              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 flex flex-col flex-1 min-h-[400px]">
                <div className="flex items-center gap-3 border-b border-gray-100 pb-4">
                  <div className="w-9 h-9 bg-violet-100 rounded-full flex items-center justify-center font-bold text-violet-600 text-xs select-none border border-violet-200">
                    I
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-gray-900">Indux Technology</h4>
                  </div>
                </div>

                <div className="py-5 space-y-4 flex-1 overflow-y-auto">
                  <h2 className="text-base font-bold text-gray-900 leading-snug break-words">
                    {subject.trim() ? renderLivePreview(subject) : "Untitled Subject Line"}
                  </h2>

                  <div className="text-xs text-gray-600 leading-relaxed font-normal break-words">
                    {body.trim() && body !== "<p></p>" ? (
                      <div
                        className="prose prose-sm max-w-none [&_strong]:font-bold [&_em]:italic [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_a]:text-violet-600 [&_a]:underline"
                        dangerouslySetInnerHTML={{ __html: renderLivePreview(body) }}
                      />
                    ) : (
                      <span className="text-gray-300 italic">body content...</span>
                    )}
                  </div>
                </div>

                <div className="border-t border-gray-100 pt-3 text-center text-[9px] text-gray-400 select-none font-medium">
                  © 2026 Indux Technology • Pune
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}