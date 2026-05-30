"use client";

import { useState, useEffect, useRef } from "react";
import { MoreVertical, Trash2, Edit2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ContactActionMenuProps {
  onDelete: () => void;
  onEdit: () => void;
}

export default function ContactActionMenu({ onDelete, onEdit }: ContactActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300 transition-colors p-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800"
      >
        <MoreVertical size={18} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -10 }}
            className="absolute right-0 mt-2 w-32 bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl shadow-xl z-20 py-1 overflow-hidden"
          >
            <button
              onClick={() => { onEdit(); setIsOpen(false); }}
              className="w-full px-4 py-2 text-left text-sm text-zinc-600 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-700/50 flex items-center gap-2"
            >
              <Edit2 size={14} /> Edit
            </button>
            <button
              onClick={() => { onDelete(); setIsOpen(false); }}
              className="w-full px-4 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-900/20 flex items-center gap-2"
            >
              <Trash2 size={14} /> Delete
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}