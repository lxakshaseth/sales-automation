"use client";
import ContactActionMenu from "./ContactActionMenu";

import { motion, Variants, AnimatePresence } from "framer-motion";
import { Mail, Phone, MapPin, Search, Plus, X } from "lucide-react";
import { useState, useEffect } from "react";

const initialContacts = [
  { id: 1, name: "Rahul Sharma", role: "CEO", company: "Tech Solutions", email: "rahul@techsolutions.com", phone: "+91 98765 43210", location: "Mumbai, India", initials: "RS", color: "bg-blue-500" },
  { id: 2, name: "Priya Patel", role: "Marketing Head", company: "Global Innovators", email: "priya@globalinnovators.com", phone: "+91 98765 43211", location: "Delhi, India", initials: "PP", color: "bg-emerald-500" },
  { id: 3, name: "Amit Kumar", role: "CTO", company: "NextGen Systems", email: "amit@nextgensystems.com", phone: "+91 98765 43212", location: "Bangalore, India", initials: "AK", color: "bg-violet-500" },
];

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } }
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export default function Contact() {
  const [allContacts, setAllContacts] = useState<any[]>([]); 
  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    name: "", role: "", company: "", email: "", phone: "", location: ""
  });

  useEffect(() => {
    const saved = localStorage.getItem("contacts-data");
    setAllContacts(saved ? JSON.parse(saved) : initialContacts);
  }, []);

  useEffect(() => {
    if (allContacts.length > 0) {
      localStorage.setItem("contacts-data", JSON.stringify(allContacts));
    }
  }, [allContacts]);

  const filteredContacts = allContacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Edit function
  const handleEdit = (contact: any) => {
    setEditingId(contact.id);
    setFormData({
      name: contact.name,
      role: contact.role,
      company: contact.company,
      email: contact.email,
      phone: contact.phone,
      location: contact.location
    });
    setIsModalOpen(true);
  };

  const handleSave = () => {
    if (!formData.name) return;

    if (editingId) {
      //Edit Logic
      const updated = allContacts.map(c => 
        c.id === editingId 
        ? { ...c, ...formData, initials: formData.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) } 
        : c
      );
      setAllContacts(updated);
    } else {
      // Add Logic
      const newContact = {
        id: Date.now(),
        ...formData,
        initials: formData.name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2),
        color: "bg-violet-500" 
      };
      setAllContacts([newContact, ...allContacts]);
    }

    // Cleanup
    setFormData({ name: "", role: "", company: "", email: "", phone: "", location: "" });
    setEditingId(null);
    setIsModalOpen(false);
  };

  const handleDelete = (id: number) => {
    setAllContacts(allContacts.filter(contact => contact.id !== id));
  };

  return (
    <div className="flex flex-col gap-8">
      {/* Header Section */}
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
          <input 
            type="text" 
            placeholder="Search contacts..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 dark:text-white transition-all"
          />
        </div>
        <button 
          onClick={() => { setEditingId(null); setFormData({name: "", role: "", company: "", email: "", phone: "", location: ""}); setIsModalOpen(true); }}
          className="w-full sm:w-auto flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm"
        >
          <Plus size={18} /> Add Contact
        </button>
      </motion.div>

      {/* Grid Section */}
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {filteredContacts.map((contact) => (
          <motion.div key={contact.id} variants={itemVariants} className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-xl transition-shadow group">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-xl ${contact.color}`}>
                  {contact.initials}
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 dark:text-white text-lg">{contact.name}</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{contact.role} at {contact.company}</p>
                </div>
              </div>
              
              {/*  Menu with Edit/Delete handlers */}
              <ContactActionMenu 
                onDelete={() => handleDelete(contact.id)} 
                onEdit={() => handleEdit(contact)} 
              />
            </div>

            <div className="space-y-3 mt-6">
              <div className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400">
                <Mail size={14} /> <span className="truncate">{contact.email}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400">
                <Phone size={14} /> <span>{contact.phone}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400">
                <MapPin size={14} /> <span>{contact.location}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Modal Section */}
      <AnimatePresence>
        {isModalOpen && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={() => setIsModalOpen(false)} className="fixed inset-0 bg-zinc-950/60 z-40 backdrop-blur-sm" />
            <motion.div initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }} className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl z-50 overflow-hidden border border-zinc-200 dark:border-zinc-800 flex flex-col max-h-[90vh]">
              <div className="flex justify-between items-center p-6 border-b border-zinc-200 dark:border-zinc-800 shrink-0">
                <h2 className="text-xl font-bold text-zinc-900 dark:text-white">
                  {editingId ? "Edit Contact" : "Add New Contact"}
                </h2>
                <button onClick={() => setIsModalOpen(false)} className="text-zinc-400 hover:text-zinc-600 p-2 rounded-full transition-colors"><X size={20} /></button>
              </div>
              
              <div className="p-6 space-y-4 overflow-y-auto">
                <div className="grid grid-cols-2 gap-5">
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Full Name</label>
                    <input type="text" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 dark:text-white transition-all" />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Role</label>
                    <input type="text" value={formData.role} onChange={(e) => setFormData({...formData, role: e.target.value})} className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none dark:text-white transition-all" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Company</label>
                    <input type="text" value={formData.company} onChange={(e) => setFormData({...formData, company: e.target.value})} className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none dark:text-white transition-all" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Email</label>
                    <input type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none dark:text-white transition-all" />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Phone Number</label>
                    <input type="tel" value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none dark:text-white transition-all" />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Location</label>
                    <input type="text" value={formData.location} onChange={(e) => setFormData({...formData, location: e.target.value})} className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none dark:text-white transition-all" />
                  </div>
                </div>
              </div>
              
              <div className="p-6 border-t border-zinc-200 dark:border-zinc-800 flex justify-end gap-3 bg-zinc-50/50 dark:bg-zinc-900/50 shrink-0">
                <button onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl transition-colors">Cancel</button>
                <button onClick={handleSave} className="px-5 py-2.5 text-sm font-medium bg-violet-600 hover:bg-violet-700 text-white rounded-xl shadow-sm transition-colors">
                  {editingId ? "Update Contact" : "Save Contact"}
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}