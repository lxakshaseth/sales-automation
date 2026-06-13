"use client";

import { useEffect, useRef, useState } from "react";

import { MoreVertical, Eye, Pencil, Trash2 } from "lucide-react";

type TemplateActionMenuProps = {
  onView: () => void;
  onEdit: () => void;
  onDelete: () => void;
};

export default function TemplateActionMenu({
  onView,
  onEdit,
  onDelete,
}: TemplateActionMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  return (
    <div ref={menuRef} className="relative inline-flex justify-center">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="h-9 w-9 rounded-xl flex items-center justify-center hover:bg-gray-100 transition-all duration-200"
      >
        <MoreVertical size={18} className="text-gray-600" />
      </button>

      <div
        className={`absolute right-0 top-11 z-50 w-44 bg-white border border-[#e7ebf3] rounded-2xl shadow-lg overflow-hidden transition-all duration-200 ${
          isOpen
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 -translate-y-2 pointer-events-none"
        }`}
      >
        <button
          onClick={() => {
            onView();
            setIsOpen(false);
          }}
          className="w-full px-4 py-3 flex items-center gap-3 text-sm text-[#111827] hover:bg-blue-50 transition-colors"
        >
          <Eye size={16} className="text-blue-600" />
          View Template
        </button>

        <button
          onClick={() => {
            onEdit();
            setIsOpen(false);
          }}
          className="w-full px-4 py-3 flex items-center gap-3 text-sm text-[#111827] hover:bg-violet-50 transition-colors"
        >
          <Pencil size={16} className="text-violet-600" />
          Edit Template
        </button>

        <div className="border-t border-[#eef2f7]" />

        <button
          onClick={() => {
            onDelete();
            setIsOpen(false);
          }}
          className="w-full px-4 py-3 flex items-center gap-3 text-sm text-red-600 hover:bg-red-50 transition-colors"
        >
          <Trash2 size={16} />
          Delete Template
        </button>
      </div>
    </div>
  );
}
