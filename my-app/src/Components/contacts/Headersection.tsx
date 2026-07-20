"use client"; //

import { useRef } from "react";
import { Search, Plus, Upload } from "lucide-react";

interface ContactsHeaderProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onAddContact: () => void;
  onImportContacts: (file: File) => Promise<void>;
  isUploading?: boolean;
}

export default function Headersection({
  searchQuery,
  onSearchChange,
  onAddContact,
  onImportContacts,
  isUploading = false,
}: ContactsHeaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.currentTarget;
    const file = input.files?.[0];
    if (!file) return;

    if (isUploading) {
      input.value = "";
      return;
    }

    try {
      await onImportContacts(file);
    } finally {
      input.value = "";
    }
  };

  return (
    <div className="bg-white border border-[#e5e7eb] border-b-0 rounded-t-2xl p-4 flex items-center justify-between shadow-sm">
      <div className="relative w-full max-w-150">
        <Search
          size={20}
          className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a3b8]"
        />
        <input
          type="text"
          placeholder="Search contacts..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          disabled={isUploading}
          className="w-full h-12 pl-12 pr-4 rounded-xl border border-[#e5e7eb] outline-none text-sm focus:ring-2 focus:ring-[#7c3aed] focus:border-transparent disabled:bg-[#f8fafc] disabled:text-[#94a3b8]"
        />
      </div>

      <div className="flex items-center gap-3 ml-5">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleImport}
          accept=".csv,text/csv"
          disabled={isUploading}
          className="hidden"
        />
        <button
          onClick={() => {
            if (!isUploading) fileInputRef.current?.click();
          }}
          disabled={isUploading}
          className="h-12 px-4 rounded-xl border border-[#e5e7eb] bg-white text-[#374151] font-medium flex items-center gap-2 hover:bg-gray-50 transition-colors disabled:opacity-60 disabled:hover:bg-white"
        >
          <Upload size={18} />
          {isUploading ? "Importing..." : "Import"}
        </button>
        <button
          onClick={onAddContact}
          disabled={isUploading}
          className="h-12 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center gap-2 hover:shadow-lg transition-all disabled:opacity-60 disabled:hover:shadow-none"
        >
          <Plus size={18} />
          Add Contact
        </button>
      </div>
    </div>
  );
}
