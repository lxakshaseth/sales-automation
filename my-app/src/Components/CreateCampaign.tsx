"use client";
import TopBar from "@/Components/Topbar";
import { useState, useEffect } from "react";
import { Mail, Send, Save, FileText, Check, Search } from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";
import { getTemplates, Template } from "@/services/template.service";
import { createCampaign } from "@/services/campaign.service";

export default function CreateCampaign() {
  const [campaignName, setCampaignName] = useState("");
  const [campaignCategory, setCampaignCategory] = useState("Promotional");
  const [scheduleDate, setScheduleDate] = useState("2025-05-28");
  const [scheduleTime, setScheduleTime] = useState("10:00");
  const [saving, setSaving] = useState(false);
  const [launching, setLaunching] = useState(false);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(true);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [templateSearch, setTemplateSearch] = useState("");

  useEffect(() => {
    async function fetchTemplates() {
      try {
        setTemplatesLoading(true);
        const res = await getTemplates();
        setTemplates(res.data);
      } catch {
        setTemplates([]);
      } finally {
        setTemplatesLoading(false);
      }
    }
    fetchTemplates();
  }, []);

  const filteredTemplates = templates.filter((t) =>
    t.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
    t.subject?.toLowerCase().includes(templateSearch.toLowerCase())
  );
  
  

 async function handleSaveDraft() {
  try {
    setSaving(true);

    const token = sessionStorage.getItem("token");

    if (!token) {
      throw new Error("Authentication token not found");
    }

    const payload = {
      name: campaignName,
      description: campaignCategory,
      status: "draft",
      funnel: [
        {
          step: "email",
          action: "welcome_email",
          waitHours: 0,
          enabled: true,
        },
      ],
      emailTemplates: selectedTemplateId
        ? [selectedTemplateId]
        : [],
    };

    await createCampaign(payload, token);

    alert("Draft saved successfully!");
  } catch (error) {
    console.error(error);

    alert(
      error instanceof Error
        ? error.message
        : "Failed to save draft"
    );
  } finally {
    setSaving(false);
  }
}

 async function handleLaunch() {
  try {
    setLaunching(true);

    const token = sessionStorage.getItem("token");

    if (!token) {
      throw new Error("User not authenticated");
    }

    const payload = {
      name: campaignName,
      description: campaignCategory,
      status: "active",
      funnel: [
        {
          step: "email",
          action: "welcome_email",
          waitHours: 0,
          enabled: true,
        },
      ],
      emailTemplates: selectedTemplateId
        ? [selectedTemplateId]
        : [],
    };

    const response = await createCampaign(payload, token);

    console.log(response);
    alert("Campaign launched successfully!");
  } catch (error) {
    console.error(error);
    alert(
      error instanceof Error
        ? error.message
        : "Failed to launch campaign"
    );
  } finally {
    setLaunching(false);
  }
}

  return (
    <div className="flex flex-col gap-8 pb-10">
      {/* Top Action Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Link href="/Campaign" className="hover:text-violet-600 transition-colors">
            Campaigns
          </Link>
          <span>/</span>
          <span className="text-zinc-900 font-medium">Create Campaign</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSaveDraft}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 border border-zinc-200 bg-white rounded-xl text-sm font-medium text-zinc-700 hover:bg-zinc-50 transition-all shadow-sm disabled:opacity-50"
          >
            <Save size={16} />
            {saving ? "Saving..." : "Save Draft"}
          </button>
          <button
            onClick={handleLaunch}
            disabled={launching}
            className="flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-700 text-white rounded-xl text-sm font-medium transition-all shadow-sm shadow-violet-600/20 disabled:opacity-50"
          >
            <Send size={16} />
            {launching ? "Launching..." : "Launch Campaign"}
          </button>
        </div>
      </div>

      {/* Page Title */}
      <div>
        <h1 className="text-3xl font-bold text-zinc-900 tracking-tight">Create New Campaign</h1>
        <p className="text-zinc-500 mt-1">Build and launch Email or WhatsApp campaigns.</p>
      </div>

      {/* Campaign Details Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8"
      >
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
            <Mail size={20} className="text-violet-600" />
          </div>
          <h2 className="text-xl font-bold text-zinc-900">Campaign Details</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Campaign Name */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">
              Campaign Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={campaignName}
              onChange={(e) => setCampaignName(e.target.value)}
              placeholder="Enter campaign name"
              className="w-full border border-zinc-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all placeholder:text-zinc-400"
            />
          </div>

          {/* Campaign Category */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">Campaign Category</label>
            <select
              value={campaignCategory}
              onChange={(e) => setCampaignCategory(e.target.value)}
              className="w-full border border-zinc-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all text-zinc-700 bg-white"
            >
              <option value="Promotional">Promotional</option>
              <option value="Transactional">Transactional</option>
              <option value="Newsletter">Newsletter</option>
              <option value="Welcome">Welcome</option>
              <option value="Re-engagement">Re-engagement</option>
            </select>
          </div>

          {/* Schedule */}
          <div>
            <label className="block text-sm font-medium text-zinc-700 mb-2">Schedule</label>
            <div className="flex gap-3">
              <input
                type="date"
                value={scheduleDate}
                onChange={(e) => setScheduleDate(e.target.value)}
                className="flex-1 border border-zinc-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all text-zinc-700"
              />
              <input
                type="time"
                value={scheduleTime}
                onChange={(e) => setScheduleTime(e.target.value)}
                className="w-36 border border-zinc-200 rounded-xl px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all text-zinc-700"
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Select Template Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="bg-white rounded-2xl border border-zinc-200 shadow-sm p-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center">
            <FileText size={20} className="text-violet-600" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-zinc-900">Select Template</h2>
            <p className="text-sm text-zinc-500">Choose an existing template for this campaign</p>
          </div>
        </div>

        {/* Search */}
        <div className="relative mt-6 mb-5">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search templates..."
            value={templateSearch}
            onChange={(e) => setTemplateSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 border border-zinc-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 transition-all placeholder:text-zinc-400"
          />
        </div>

        {/* Templates Grid */}
        {templatesLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="animate-pulse h-28 bg-zinc-100 rounded-xl" />
            ))}
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-14 border border-dashed border-zinc-200 rounded-xl">
            <div className="w-12 h-12 rounded-xl bg-violet-50 flex items-center justify-center mb-3">
              <FileText size={22} className="text-violet-400" />
            </div>
            <p className="text-zinc-500 text-sm font-medium">No templates found</p>
            <Link href="/templates" className="mt-2 text-xs text-violet-600 hover:underline">
              Go to Templates to create one
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => {
              const isSelected = selectedTemplateId === template._id;
              return (
                <button
                  key={template._id}
                  onClick={() => setSelectedTemplateId(isSelected ? null : template._id)}
                  className={`relative text-left p-4 rounded-xl border-2 transition-all duration-200 group ${
                    isSelected
                      ? "border-violet-500 bg-violet-50 shadow-sm shadow-violet-100"
                      : "border-zinc-200 hover:border-violet-300 hover:bg-zinc-50"
                  }`}
                >
                  {isSelected && (
                    <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-violet-600 flex items-center justify-center">
                      <Check size={11} className="text-white" strokeWidth={3} />
                    </span>
                  )}
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                      template.type === "email"
                        ? "bg-blue-100 text-blue-700"
                        : template.type === "sms"
                        ? "bg-green-100 text-green-700"
                        : "bg-orange-100 text-orange-700"
                    }`}>
                      {template.type.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-zinc-900 truncate">{template.name}</p>
                  {template.subject && (
                    <p className="text-xs text-zinc-500 mt-1 truncate">{template.subject}</p>
                  )}
                </button>
              );
            })}
          </div>
        )}

        {selectedTemplateId && (
          <p className="mt-4 text-xs text-violet-600 font-medium">
            ✓ Template selected: {templates.find((t) => t._id === selectedTemplateId)?.name}
          </p>
        )}
      </motion.div>
    </div>
  );
}