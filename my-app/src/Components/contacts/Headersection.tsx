"use client";

import { useRef } from "react";
import { Search, Plus, Upload } from "lucide-react";
import { bulkUploadContacts } from "@/services/contact.service";

interface ContactsHeaderProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onAddContact: () => void;
  onImportSuccess?: () => void;
}

export default function Headersection({
  searchQuery,
  onSearchChange,
  onAddContact,
  onImportSuccess,
}: ContactsHeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const data = await bulkUploadContacts(file);
      alert(`${data.totalUploaded} contacts imported successfully!`);
      onImportSuccess?.();
    } catch (err: any) {
      alert(err.message || "Import failed");
    }
    e.target.value = "";
  };

  return (
    <div className="bg-white border border-[#e5e7eb] rounded-2xl p-4 flex items-center justify-between shadow-sm">
      <div className="relative w-full max-w-[600px]">
        <Search
          size={20}
          className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a3b8]"
        />
        <input
          type="text"
          placeholder="Search contacts..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full h-12 pl-12 pr-4 rounded-xl border border-[#e5e7eb] outline-none text-sm focus:ring-2 focus:ring-[#7c3aed] focus:border-transparent"
        />
      </div>

      <div className="flex items-center gap-3 ml-5">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImport}
          accept=".csv"
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          className="h-12 px-4 rounded-xl border border-[#e5e7eb] bg-white text-[#374151] font-medium flex items-center gap-2 hover:bg-gray-50 transition-colors"
        >
          <Upload size={18} />
          Import
        </button>
        <button
          onClick={onAddContact}
          className="h-12 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center gap-2 hover:shadow-lg transition-all"
        >
          <Plus size={18} />
          Add Contact
        </button>
      </div>
    </div>
  );
}
