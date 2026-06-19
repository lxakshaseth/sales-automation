"use client";

import { Bell } from "lucide-react";

interface TopBarProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
}

export default function TopBar({
  title,
  description,
  children,
}: TopBarProps) {
  return (
    <div className="flex items-start justify-between gap-6 border-b border-slate-200 pb-4">
      <div>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">
          {title}
        </h1>

        {description && (
          <p className="mt-1 text-slate-500 text-sm">
            {description}
          </p>
        )}
      </div>

      <div className="flex items-center gap-4 shrink-0">
        {children}

        <button className="relative p-2 rounded-xl hover:bg-slate-100 transition">
          <Bell className="w-8 h-8 text-slate-600" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-violet-600" />
        </button>

        <button className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600" />

          <div className="hidden lg:block text-left">
            <p className="text-sm font-semibold">
              Admin
            </p>
            <p className="text-xs text-slate-500">
              Administrator
            </p>
          </div>
        </button>
      </div>
    </div>
  );
}