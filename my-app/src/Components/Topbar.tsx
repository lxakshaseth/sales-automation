"use client";

import { Bell, LogOut, User } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";

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
  const [showProfileMenu, setShowProfileMenu] = useState(false);

const router = useRouter();

const handleLogout = () => {
  sessionStorage.removeItem("token");
  toast.success("Logout Successfully");
  router.push("/sign-in");
};
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

        <div className="relative">
  <button
    onClick={() => setShowProfileMenu(!showProfileMenu)}
    className="flex items-center gap-2"
  >
    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-semibold">
      A
    </div>

    <div className="hidden lg:block text-left">
      <p className="text-sm font-semibold">
        Admin
      </p>
      <p className="text-xs text-slate-500">
        Administrator
      </p>
    </div>
  </button>

  {showProfileMenu && (
    <div className="absolute right-0 top-14 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">

      <button
        className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 text-left"
      >
        <User size={18} />
        <span>Profile</span>
      </button>

      <button
        onClick={handleLogout}
        className="w-full px-4 py-3 flex items-center gap-3 hover:bg-red-50 text-red-600 text-left"
      >
        <LogOut size={18} />
        <span>Logout</span>
      </button>

    </div>
  )}
</div>
      </div>
    </div>
  );
}