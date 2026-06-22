"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowLeft, Save, Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import TemplateEditor from "./TemplateEditor";
import { createTemplate, updateTemplate } from "@/services/template.service";

type VariableItem = {
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
  const [type, setType] = useState("email");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [editor, setEditor] = useState<any>(null);
  
  const [bodyVariables, setBodyVariables] = useState<VariableItem[]>([]);
  
  const [previewFirstName, setPreviewFirstName] = useState("Arpita");
  const [previewLastName, setPreviewLastName] = useState("Kulkarni");

  const subjectInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (initialData) {
      setName(initialData.name || "");
      setType(initialData.type || "email");
      setSubject(initialData.subject || "");
      setBody(initialData.body || "");
      setBodyVariables(initialData.dynamicVariables || []);
    } else {
      setName("");
      setType("email");
      setSubject("");
      setBody("");
      setBodyVariables([]);
    }
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  // Insert variable into subject line
  const handleSubjectVariableClick = (variableToken: string) => {
    const input = subjectInputRef.current;
    if (!input) return;

    const start = input.selectionStart || 0;
    const end = input.selectionEnd || 0;
    const updatedSubject = subject.substring(0, start) + variableToken + subject.substring(end);
    
    setSubject(updatedSubject);

    setTimeout(() => {
      input.focus();
      const newCursorPos = start + variableToken.length;
      input.setSelectionRange(newCursorPos, newCursorPos);
    }, 10);
  };

  // Insert variable into body editor
  const handleBodyVariableClick = (variableId: string) => {
    if (editor) {
      editor.chain().focus().insertContent(`{{${variableId}}}`).run();
    }
  };

  const handleAddBodyVariable = () => {
    setBodyVariables((prev) => {
      const nextId = prev.length + 1;
      return [...prev, { id: `custom_${nextId}`, label: `Variable ${nextId}`, value: "" }];
    });
  };

  const handleRemoveBodyVariable = (id: string) => {
    setBodyVariables((prev) => prev.filter((v) => v.id !== id));
  };

  const handleBodyVariableValueChange = (id: string, newValue: string) => {
    setBodyVariables((prev) =>
      prev.map((v) => (v.id === id ? { ...v, value: newValue } : v))
    );
  };

  // Parse variables for live preview matching
  function renderLivePreview(rawText: string) {
    let processText = rawText;
    
    processText = processText.replace(/{{firstName}}/g, previewFirstName || "{{firstName}}");
    processText = processText.replace(/{{lastName}}/g, previewLastName || "{{lastName}}");
    
    bodyVariables.forEach((variable) => {
      const placeholderStr = `{{${variable.id}}}`;
      const escapeRegex = placeholderStr.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
      const regex = new RegExp(escapeRegex, "g");
      processText = processText.replace(regex, variable.value.trim() !== "" ? variable.value : placeholderStr);
    });
    
    return processText;
  }

  async function handleSubmit() {
    if (!name.trim()) {
      toast.error("Please enter a template name");
      return;
    }
    try {
      loading || setLoading(true);
      setError("");

      const templatePayload = {
        name,
        type,
        subject,
        body,
        dynamicVariables: bodyVariables,
      };

      if (initialData?._id) {
        await updateTemplate(initialData._id, templatePayload);
        toast.success("Template updated successfully");
      } else {
        await createTemplate(templatePayload);
        toast.success("Template created successfully");
      }

      onSuccess();
      onClose();
    } catch {
      toast.error("Failed to save template workspace changes");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-[#f8fafc] flex flex-col rounded-3xl border border-[#e7ebf3] bg-white overflow-hidden min-h-[calc(100vh-120px)] animate-in fade-in duration-150">
      {/* HEADER SECTION */}
      <div className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-xl text-gray-500 hover:text-gray-800 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="new_email_template"
                className="text-base font-bold text-gray-900 bg-transparent border-b border-transparent hover:border-gray-200 focus:border-violet-500 outline-none transition-all py-0.5 px-1 min-w-[180px]"
              />
            </div>
            <p className="text-[11px] text-gray-400 font-medium px-1">Indux Sales Automation</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="h-9 px-3 text-xs font-semibold text-gray-700 bg-white border border-gray-200 rounded-xl outline-none focus:ring-2 focus:ring-violet-500/20"
          >
            <option value="email">Email Template</option>
            <option value="sms">SMS Template</option>
            <option value="ai_call">AI Call Template</option>
          </select>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white font-semibold rounded-xl text-xs flex items-center gap-1.5 transition-all shadow-sm disabled:opacity-50"
          >
            <Save size={14} />
            {loading ? "Saving..." : initialData ? "Update Template" : "Save Template"}
          </button>
        </div>
      </div>

      {/* MAIN WORKSPACE GRID */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 bg-[#fdfeff]">
        {/* LEFT WORKSPACE PANEL */}
        <div className="lg:col-span-7 p-6 space-y-5 border-r border-gray-100 bg-white flex flex-col justify-stretch">
          <div className="flex items-center border-b border-gray-100 py-2.5 px-1">
            <span className="text-sm font-semibold text-gray-400 w-16 select-none">From:</span>
            <span className="text-sm font-medium text-gray-700 font-mono">support@induxtechnology</span>
          </div>

          {/* SUBJECT VARIABLES */}
          <div className="space-y-2 bg-slate-50/60 p-3 rounded-xl border border-slate-100">
            <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Add Subject Variables:</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleSubjectVariableClick("{{firstName}}")}
                className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-white text-indigo-600 border border-indigo-100 hover:border-indigo-300 shadow-sm transition-all"
              >
                + First Name
              </button>
              <button
                type="button"
                onClick={() => handleSubjectVariableClick("{{lastName}}")}
                className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-white text-indigo-600 border border-indigo-100 hover:border-indigo-300 shadow-sm transition-all"
              >
                + Last Name
              </button>
            </div>
          </div>

          <div className="flex items-center border-b border-gray-100 py-2 px-1">
            <span className="text-sm font-semibold text-gray-400 w-16 select-none">Subject:</span>
            <input
              ref={subjectInputRef}
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Enter email subject line..."
              className="flex-1 text-sm font-medium text-gray-800 bg-transparent outline-none placeholder:text-gray-400"
            />
          </div>
          
          {/* BODY VARIABLES */}
          <div className="space-y-3 bg-violet-50/40 p-4 rounded-2xl border border-violet-100/60">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Add Body Variables</h3>
                <p className="text-[11px] text-gray-400 mt-0.5">Click a variable token box to insert it inside the editor workflow below</p>
              </div>
              <button
                type="button"
                onClick={handleAddBodyVariable}
                className="h-8 px-3 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm"
              >
                <Plus size={14} />
                Add Custom Variable
              </button>
            </div>

            {bodyVariables.length === 0 ? (
              <p className="text-xs text-gray-400 italic py-0.5">No custom body variables added yet</p>
            ) : (
              <div className="flex flex-wrap gap-2 pt-1">
                {bodyVariables.map((variable) => (
                  <button
                    key={variable.id}
                    type="button"
                    onClick={() => handleBodyVariableClick(variable.id)}
                    className="px-3 py-1.5 text-xs font-bold rounded-xl bg-white text-violet-600 border border-violet-200 shadow-sm hover:border-violet-400 transition-all"
                  >
                    {"{{"}
                    {variable.id}
                    {"}}"}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <div className="flex-1 min-h-[240px]">
            <TemplateEditor
              content={body}
              onChange={setBody}
              onEditorReady={setEditor}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3 text-xs text-red-600 font-medium">
              {error}
            </div>
          )}
        </div>

        {/* RIGHT LIVE PREVIEW PANEL */}
        <div className="lg:col-span-5 bg-[#f8fafc] p-6 flex flex-col justify-start border-l border-gray-50 space-y-4">
          
          {/* SIMULATION INPUTS */}
          <div className="bg-white p-4 rounded-2xl border border-gray-200/60 shadow-sm space-y-3">
            <div>
              <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Configure variable Values</h4>
              <p className="text-[10px] text-gray-400">Fill standard fields or custom variables below for personalization</p>
            </div>

            <div className="space-y-2 max-h-[180px] overflow-y-auto pr-1">
              {/* Default Lead Fields */}
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500 font-mono">{"{{firstName}}"}</label>
                  <input
                    type="text"
                    value={previewFirstName}
                    onChange={(e) => setPreviewFirstName(e.target.value)}
                    className="w-full text-xs border border-gray-200 rounded-lg px-2 py-1.5 outline-none focus:border-violet-500"
                    placeholder="e.g. Arpita"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-bold text-gray-500 font-mono">{"{{lastName}}"}</label>
                  <input
                    type="text"
                    value={previewLastName}
                    onChange={(e) => setPreviewLastName(e.target.value)}
                    className="w-full text-xs border border-gray-200 rounded-lg px-2 py-1.5 outline-none focus:border-violet-500"
                    placeholder="e.g. Kulkarni"
                  />
                </div>
              </div>

              {/* Custom Variables Rendering Inputs */}
              {bodyVariables.map((variable) => (
                <div key={variable.id} className="flex items-center gap-2 bg-gray-50/50 p-1.5 rounded-lg border border-gray-100">
                  <span className="text-[10px] font-mono text-violet-600 font-bold min-w-[75px] truncate">
                    {"{{"}{variable.id}{"}}"}
                  </span>
                  <input
                    type="text"
                    value={variable.value}
                    onChange={(e) => handleBodyVariableValueChange(variable.id, e.target.value)}
                    className="flex-1 text-xs border border-gray-200 rounded-lg px-2 py-1 outline-none bg-white focus:border-violet-500"
                    placeholder="Custom text..."
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveBodyVariable(variable.id)}
                    className="text-gray-400 hover:text-red-500 p-1"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* LIVE CANVAS SCREEN */}
          <div className="flex flex-col flex-1">
            <div className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-2 select-none">
              ✉️ Live Canvas Preview
            </div>

            <div className="w-full border border-gray-200/80 rounded-2xl bg-white shadow-md flex flex-col overflow-hidden min-h-[380px] p-6">
              <div className="flex items-center gap-3 border-b border-gray-50 pb-4">
                <div className="w-9 h-9 bg-violet-100 rounded-full flex items-center justify-center font-bold text-violet-600 text-xs select-none">
                  I
                </div>
                <div>
                  <h4 className="text-xs font-bold text-gray-900">Indux Technology </h4>
        
                </div>
              </div>

              <div className="py-5 space-y-4 flex-1 overflow-y-auto">
                <h2 className="text-base font-bold text-gray-900 leading-snug break-words">
                  {subject.trim() ? renderLivePreview(subject) : "Untitled Subject Line"}
                </h2>

                <div className="text-xs text-gray-600 leading-relaxed font-normal break-words">
                  {body.trim() && body !== "<p></p>" ? (
                    <div
                      className="prose prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: renderLivePreview(body) }}
                    />
                  ) : (
                    <span className="text-gray-300 italic">body content...</span>
                  )}
                </div>
              </div>

              <div className="border-t border-gray-50 pt-3 text-center text-[9px] text-gray-400 select-none font-medium">
                © 2026 Indux Technology • Pune
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}