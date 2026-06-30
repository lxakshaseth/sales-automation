"use client";

import { motion } from "framer-motion";
import { LogOut, User, ChevronDown } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import ProfileModal from "@/Components/ProfileModal";

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
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [user, setUser] = useState({
    name: "",
    role: "",
  });

  const router = useRouter();

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    toast.success("Logout Successfully");
    router.push("/sign-in");
  };

  const handleCloseProfile = () => {
    setShowProfileModal(false);
  };

  useEffect(() => {
    const stored = sessionStorage.getItem("user");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setUser({
          name: parsed.name || "",
          role: parsed.role || "",
        });
      } catch {
        // ignore
      }
    }
  }, []);

  const initials = useMemo(() => {
    const names = user.name.trim().split(" ").filter(Boolean);
    if (names.length === 0) return "";
    if (names.length === 1) return names[0].charAt(0).toUpperCase();
    return (
      names[0].charAt(0).toUpperCase() +
      names[names.length - 1].charAt(0).toUpperCase()
    );
  }, [user.name]);

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex items-start justify-between gap-6 border-b border-slate-200 pb-4"
      >
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
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2.5 hover:bg-transparent"
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                {initials}
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-sm font-semibold">
                  {user.name}
                </p>
              </div>

              <ChevronDown
                size={16}
                className={`text-gray-500 transition-transform ${
                  showProfileMenu ? "rotate-180" : ""
                }`}
              />
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-52 overflow-hidden rounded-xl border border-[#e2e8f0] bg-white py-1.5 shadow-lg shadow-black/5">
                <button
                  onClick={() => {
                    setShowProfileModal(true);
                    setShowProfileMenu(false);
                  }}
                  className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-[13px] text-[#0f172a] transition-colors hover:bg-[#f8fafc]"
                >
                  <User size={18} />
                  <span>Profile</span>
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-[13px] text-[#dc2626] transition-colors hover:bg-[#fef2f2]"
                >
                  <LogOut size={18} />
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      <ProfileModal
        isOpen={showProfileModal}
        onClose={handleCloseProfile}
        onProfileUpdated={(profile) => setUser(profile)}
      />
    </>
  );
}