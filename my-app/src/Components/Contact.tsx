"use client";

import { motion, Variants, AnimatePresence } from "framer-motion";
import { Mail, Phone, MapPin, MoreVertical, Search, Plus, X } from "lucide-react";
import { useState } from "react";

const contacts = [
  { id: 1, name: "Rahul Sharma", role: "CEO", company: "Tech Solutions", email: "rahul@techsolutions.com", phone: "+91 98765 43210", location: "Mumbai, India", initials: "RS", color: "bg-blue-500" },
  { id: 2, name: "Priya Patel", role: "Marketing Head", company: "Global Innovators", email: "priya@globalinnovators.com", phone: "+91 98765 43211", location: "Delhi, India", initials: "PP", color: "bg-emerald-500" },
  { id: 3, name: "Amit Kumar", role: "CTO", company: "NextGen Systems", email: "amit@nextgensystems.com", phone: "+91 98765 43212", location: "Bangalore, India", initials: "AK", color: "bg-violet-500" },
  { id: 4, name: "Sneha Gupta", role: "Product Manager", company: "Alpha Corp", email: "sneha@alphacorp.com", phone: "+91 98765 43213", location: "Pune, India", initials: "SG", color: "bg-rose-500" },
  { id: 5, name: "Vikram Singh", role: "Sales Director", company: "Pioneer Tech", email: "vikram@pioneertech.com", phone: "+91 98765 43214", location: "Hyderabad, India", initials: "VS", color: "bg-orange-500" },
  { id: 6, name: "Neha Verma", role: "HR Manager", company: "Future Works", email: "neha@futureworks.com", phone: "+91 98765 43215", location: "Chennai, India", initials: "NV", color: "bg-pink-500" },
];

// Framer Motion Variants for staggering children
const containerVariants: Variants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 } // Delays each card by 0.1s
  }
};

// Framer Motion Variants for individual cards
const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

export default function Contact() {
  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  const filteredContacts = contacts.filter(contact =>
    contact.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex flex-col gap-8">
      {/* Top Actions - Slides down from top */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="flex flex-col sm:flex-row justify-between items-center gap-4 bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm"
      >
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400 w-5 h-5" />
          <input 
            type="text" 
            placeholder="Search contacts by name or company..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all"
          />
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="w-full sm:w-auto flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm shadow-violet-600/20"
        >
          <Plus size={18} />
          Add Contact
        </button>
      </motion.div>

      {/* Contact Grid - Cascading fade-up animation */}
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6"
      >
        {filteredContacts.map((contact) => (
          <motion.div 
            key={contact.id}
            variants={itemVariants}
            whileHover={{ y: -5, transition: { duration: 0.2 } }}
            className="bg-white dark:bg-zinc-900 rounded-2xl p-6 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-xl hover:shadow-zinc-200/20 dark:hover:shadow-black/40 transition-shadow group"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-xl shadow-inner ${contact.color}`}>
                  {contact.initials}
                </div>
                <div>
                  <h3 className="font-semibold text-zinc-900 dark:text-white text-lg">{contact.name}</h3>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{contact.role} at <span className="font-medium text-zinc-700 dark:text-zinc-300">{contact.company}</span></p>
                </div>
              </div>
              <button className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800">
                <MoreVertical size={18} />
              </button>
            </div>
            
            <div className="space-y-3 mt-6">
              <div className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-200 transition-colors">
                <div className="w-8 h-8 rounded-full bg-zinc-50 dark:bg-zinc-800/50 flex items-center justify-center shrink-0">
                  <Mail size={14} />
                </div>
                <span className="truncate">{contact.email}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-200 transition-colors">
                <div className="w-8 h-8 rounded-full bg-zinc-50 dark:bg-zinc-800/50 flex items-center justify-center shrink-0">
                  <Phone size={14} />
                </div>
                <span>{contact.phone}</span>
              </div>
              <div className="flex items-center gap-3 text-sm text-zinc-600 dark:text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-zinc-200 transition-colors">
                <div className="w-8 h-8 rounded-full bg-zinc-50 dark:bg-zinc-800/50 flex items-center justify-center shrink-0">
                  <MapPin size={14} />
                </div>
                <span>{contact.location}</span>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Add Contact Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsModalOpen(false)}
              className="fixed inset-0 bg-zinc-950/60 z-40 backdrop-blur-sm"
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-lg bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl z-50 overflow-hidden border border-zinc-200 dark:border-zinc-800 flex flex-col max-h-[90vh]"
            >
              <div className="flex justify-between items-center p-6 border-b border-zinc-200 dark:border-zinc-800 shrink-0">
                <h2 className="text-xl font-bold text-zinc-900 dark:text-white tracking-tight">Add New Contact</h2>
                <button onClick={() => setIsModalOpen(false)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 p-2 rounded-full transition-colors">
                  <X size={20} />
                </button>
              </div>
              
              <div className="p-6 space-y-4 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800">
                <div className="grid grid-cols-2 gap-5">
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Full Name</label>
                    <input type="text" className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all" placeholder="e.g. John Doe" />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Role</label>
                    <input type="text" className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all" placeholder="e.g. Manager" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Company</label>
                    <input type="text" className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all" placeholder="e.g. Acme Corp" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Email</label>
                    <input type="email" className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all" placeholder="e.g. john@example.com" />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Phone Number</label>
                    <input type="tel" className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all" placeholder="+1 (555) 000-0000" />
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">Location</label>
                    <input type="text" className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-500 dark:text-white transition-all" placeholder="e.g. New York, USA" />
                  </div>
                </div>
              </div>
              
              <div className="p-6 border-t border-zinc-200 dark:border-zinc-800 flex justify-end gap-3 bg-zinc-50/50 dark:bg-zinc-900/50 shrink-0">
                <button onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-sm font-medium text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-xl transition-colors">Cancel</button>
                <button onClick={() => setIsModalOpen(false)} className="px-5 py-2.5 text-sm font-medium bg-violet-600 hover:bg-violet-700 text-white rounded-xl shadow-sm shadow-violet-600/20 transition-colors">Save Contact</button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}