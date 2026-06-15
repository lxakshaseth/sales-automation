"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MoreHorizontal, ChevronLeft, ChevronRight, Copy, Bell, Maximize2, Search, Plus, Upload, Download, Edit3, Trash2, X } from "lucide-react";

const initialContacts = [
  { id: 1, name: "Rahul Sharma", phone: "+91 98765 43210", email: "rahul.sharma@gmail.com", company: "NexaTech Solutions" },
  { id: 2, name: "Priya Patel", phone: "+91 87654 32109", email: "priya.patel@yahoo.com", company: "SolarNest Energy" },
  { id: 3, name: "Amit Kumar", phone: "+91 76543 21098", email: "amit.kumar@gmail.com", company: "Horizon Getaways" },
  { id: 4, name: "Sneha Gupta", phone: "+91 65432 10987", email: "sneha.gupta@gmail.com", company: "PrimeTrust" },
  { id: 5, name: "Vikram Singh", phone: "+91 54321 09876", email: "vikram.singh@gmail.com", company: "SolarNest Energy" },
  { id: 6, name: "Neha Reddy", phone: "+91 43210 98765", email: "neha.reddy@gmail.com", company: "PureTaste Organics" },
  { id: 7, name: "Rajesh Khanna", phone: "+91 32109 87654", email: "rajesh.khanna@outlook.com", company: "Skyline Estates" },
  { id: 8, name: "Anjali Desai", phone: "+91 21098 76543", email: "anjali.desai@gmail.com", company: "Skyline Estates" },
  { id: 9, name: "Sunil Verma", phone: "+91 10987 65432", email: "sunil.verma@gmail.com", company: "NexaTech Solutions" },
  { id: 10, name: "Deepika Nair", phone: "+91 99887 66554", email: "deepika.nair@gmail.com", company: "EcoDrive" },
  { id: 11, name: "Manoj Tiwari", phone: "+91 88776 55443", email: "manoj.tiwari@gmail.com", company: "PureTaste Organics" },
  { id: 12, name: "Kavita Joshi", phone: "+91 77665 44332", email: "kavita.joshi@gmail.com", company: "HorizonTrust" },
];

const PAGE_SIZE = 11;

const IndiaFlag = () => (
  <div className="w-5 h-5 rounded-full overflow-hidden flex-shrink-0 border border-zinc-200">
    <div className="h-1/3 bg-orange-500" />
    <div className="h-1/3 bg-white flex items-center justify-center">
      <div className="w-1.5 h-1.5 rounded-full bg-blue-800" />
    </div>
    <div className="h-1/3 bg-green-600" />
  </div>
);

interface Contact {
  id: number;
  name: string;
  phone: string;
  email: string;
  company: string;
}

export default function Contactlist() {
  const [contacts, setContacts] = useState<Contact[]>(initialContacts);
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(1);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [activeDropdown, setActiveDropdown] = useState<number | null>(null);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [deletingContact, setDeletingContact] = useState<Contact | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setActiveDropdown(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filter contacts by search
  const filtered = contacts.filter(c =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.phone.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleCopy = (email: string, id: number) => {
    navigator.clipboard.writeText(email);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  // Import contacts from JSON file
  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const imported = JSON.parse(event.target?.result as string);
        if (Array.isArray(imported)) {
          setContacts(prev => [...prev, ...imported]);
          alert(`Imported ${imported.length} contacts successfully!`);
        }
      } catch {
        alert("Invalid JSON file");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  // Export contacts to JSON file
  const handleExport = () => {
    const dataStr = JSON.stringify(contacts, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "contacts.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Delete contact
  const handleDelete = () => {
    if (!deletingContact) return;
    setContacts(prev => prev.filter(c => c.id !== deletingContact.id));
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      newSet.delete(deletingContact.id);
      return newSet;
    });
    setDeletingContact(null);
    setActiveDropdown(null);
  };

  // Toggle select all on current page
  const toggleSelectAll = () => {
    const pageIds = paginated.map(c => c.id);
    const allSelected = pageIds.every(id => selectedIds.has(id));
    
    if (allSelected) {
      // Deselect all on this page
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        pageIds.forEach(id => newSet.delete(id));
        return newSet;
      });
    } else {
      // Select all on this page
      setSelectedIds(prev => {
        const newSet = new Set(prev);
        pageIds.forEach(id => newSet.add(id));
        return newSet;
      });
    }
  };

  // Toggle single contact
  const toggleContact = (id: number) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Edit contact
  const handleEdit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingContact) return;
    setContacts(prev => prev.map(c => c.id === editingContact.id ? editingContact : c));
    setEditingContact(null);
    setActiveDropdown(null);
  };

  return (
    <div>
      {/* HEADER SECTION */}
      <div>
        {/* TOP HEADER */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-[40px] font-bold text-[#111827]">
                Contacts Directory
              </h1>
              <p className="mt-2 text-[15px] text-[#64748b]">
                Manage your clients, leads, and team members.
              </p>
            </div>
            <div className="flex items-center gap-5">
              <div className="relative">
                <Bell size={24} className="text-[#64748b]" />
                <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-red-500 text-white text-[10px] flex items-center justify-center font-semibold">
                  6
                </span>
              </div>
              <Maximize2 size={18} className="text-[#64748b]" />
              <div className="w-10 h-10 rounded-full bg-[#3b82f6] flex items-center justify-center text-white font-semibold">
                N
              </div>
            </div>
          </div>
        </motion.div>

        {/* SEARCH BAR */}
        <div className="bg-white border border-[#e5e7eb] rounded-2xl p-4 flex items-center justify-between shadow-sm">
          <div className="relative w-full max-w-[600px]">
            <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#94a3b8]" />
            <input
              type="text"
              placeholder="Search contacts..."
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
              className="w-full h-12 pl-12 pr-4 rounded-xl border border-[#e5e7eb] outline-none text-sm"
            />
          </div>
          <div className="flex items-center gap-3 ml-5">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImport}
              accept=".json"
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
              onClick={handleExport}
              className="h-12 px-4 rounded-xl border border-[#e5e7eb] bg-white text-[#374151] font-medium flex items-center gap-2 hover:bg-gray-50 transition-colors"
            >
              <Download size={18} />
              Export
            </button>
            <button className="h-12 px-6 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center gap-2">
              <Plus size={18} />
              Add Contact
            </button>
          </div>
        </div>
      </div>

      {/* CONTACTS TABLE */}
      <div className="mt-6 bg-white rounded-2xl border border-zinc-200 shadow-sm overflow-hidden">
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-zinc-50 border-b border-zinc-100">
              <th className="w-10 px-4 py-3">
                <input 
                  type="checkbox" 
                  checked={paginated.length > 0 && paginated.every(c => selectedIds.has(c.id))}
                  onChange={toggleSelectAll}
                  className="rounded border-zinc-300 accent-violet-600 cursor-pointer" 
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide">Name</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide">Phone</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide">Email</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide">Company</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-500 uppercase tracking-wide">Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((contact) => (
              <motion.tr
                key={contact.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors"
              >
                <td className="px-4 py-3">
                  <input 
                    type="checkbox" 
                    checked={selectedIds.has(contact.id)}
                    onChange={() => toggleContact(contact.id)}
                    className="rounded border-zinc-300 accent-violet-600 cursor-pointer" 
                  />
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center text-sm font-semibold text-violet-600">
                      {contact.name.split(" ").map(n => n[0]).join("")}
                    </div>
                    <span className="text-sm font-medium text-zinc-900">{contact.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <IndiaFlag />
                    <span className="text-sm text-zinc-600">{contact.phone}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-zinc-600">{contact.email}</span>
                    <button
                      onClick={() => handleCopy(contact.email, contact.id)}
                      className="p-1 rounded hover:bg-zinc-100 transition-colors"
                    >
                      {copiedId === contact.id ? (
                        <span className="text-xs text-green-600">Copied!</span>
                      ) : (
                        <Copy size={12} className="text-zinc-400" />
                      )}
                    </button>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-zinc-600">{contact.company}</span>
                </td>
                <td className="px-4 py-3 relative">
                  <div ref={activeDropdown === contact.id ? dropdownRef : null}>
                    <button 
                      onClick={() => setActiveDropdown(activeDropdown === contact.id ? null : contact.id)}
                      className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 transition-colors"
                    >
                      <MoreHorizontal size={16} />
                    </button>
                    <AnimatePresence>
                      {activeDropdown === contact.id && (
                        <motion.div
                          initial={{ opacity: 0, y: 5, scale: 0.95 }}
                          animate={{ opacity: 1, y: 0, scale: 1 }}
                          exit={{ opacity: 0, y: 5, scale: 0.95 }}
                          className="absolute right-0 top-full mt-1 w-36 bg-white rounded-xl shadow-lg border border-zinc-200 py-1 z-50"
                        >
                          <button
                            onClick={() => setEditingContact(contact)}
                            className="w-full px-4 py-2 text-left text-sm text-zinc-700 hover:bg-zinc-50 flex items-center gap-2"
                          >
                            <Edit3 size={14} />
                            Edit
                          </button>
                          <button
                            onClick={() => setDeletingContact(contact)}
                            className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                          >
                            <Trash2 size={14} />
                            Delete
                          </button>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-5 py-4 border-t border-zinc-100">
        <div className="flex items-center gap-2">
          <span className="text-sm text-zinc-500">Items Per Page</span>
          <select className="text-sm border border-zinc-200 rounded-lg px-2 py-1 bg-white outline-none">
            <option>11</option>
            <option>20</option>
            <option>50</option>
          </select>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => i + 1).map(n => (
              <button
                key={n}
                onClick={() => setPage(n)}
                className={`w-7 h-7 rounded-lg text-sm font-medium transition-colors ${
                  page === n ? "bg-zinc-900 text-white" : "text-zinc-500 hover:bg-zinc-100"
                }`}
              >
                {n}
              </button>
            ))}
            {totalPages > 10 && <span className="px-2 text-zinc-400">...</span>}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 disabled:opacity-40 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>
      </div>

      {/* EDIT MODAL */}
      <AnimatePresence>
        {editingContact && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setEditingContact(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 w-full max-w-md"
            >
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-zinc-900">Edit Contact</h2>
                <button onClick={() => setEditingContact(null)} className="p-1 rounded-lg hover:bg-zinc-100">
                  <X size={20} className="text-zinc-500" />
                </button>
              </div>
              <form onSubmit={handleEdit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Name</label>
                  <input
                    type="text"
                    value={editingContact.name}
                    onChange={(e) => setEditingContact({ ...editingContact, name: e.target.value })}
                    className="w-full h-11 px-3 rounded-xl border border-zinc-200 outline-none text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Phone</label>
                  <input
                    type="text"
                    value={editingContact.phone}
                    onChange={(e) => setEditingContact({ ...editingContact, phone: e.target.value })}
                    className="w-full h-11 px-3 rounded-xl border border-zinc-200 outline-none text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={editingContact.email}
                    onChange={(e) => setEditingContact({ ...editingContact, email: e.target.value })}
                    className="w-full h-11 px-3 rounded-xl border border-zinc-200 outline-none text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-zinc-700 mb-1">Company</label>
                  <input
                    type="text"
                    value={editingContact.company}
                    onChange={(e) => setEditingContact({ ...editingContact, company: e.target.value })}
                    className="w-full h-11 px-3 rounded-xl border border-zinc-200 outline-none text-sm"
                  />
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setEditingContact(null)}
                    className="flex-1 h-11 rounded-xl border border-zinc-200 text-zinc-700 font-medium hover:bg-zinc-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 h-11 rounded-xl bg-violet-600 text-white font-medium hover:bg-violet-700"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* DELETE CONFIRMATION MODAL */}
      <AnimatePresence>
        {deletingContact && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
            onClick={() => setDeletingContact(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 w-full max-w-sm text-center"
            >
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                <Trash2 size={24} className="text-red-600" />
              </div>
              <h2 className="text-xl font-semibold text-zinc-900 mb-2">Delete Contact?</h2>
              <p className="text-zinc-500 mb-6">
                Are you sure you want to delete <strong>{deletingContact.name}</strong>? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setDeletingContact(null)}
                  className="flex-1 h-11 rounded-xl border border-zinc-200 text-zinc-700 font-medium hover:bg-zinc-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  className="flex-1 h-11 rounded-xl bg-red-600 text-white font-medium hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}