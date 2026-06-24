import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

import { LogOut, ChevronDown } from "lucide-react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";

interface User {
  name: string;
  email: string;
  role: string;
}

function getInitials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

export function DashboardHeader() {
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    const stored = sessionStorage.getItem("user");
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        setUser(null);
      }
    }
  }, []);

  // Close the profile menu when clicking outside it
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowProfileMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    toast.success("Logged out successfully");
    router.push("/sign-in");
  };

  const displayName = user?.name ?? "Guest";
  const displayEmail = user?.email ?? "";
  const displayRole = user?.role ?? "";
  const initials = user?.name ? getInitials(user.name) : "?";

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-8 flex items-start justify-between gap-6 rounded-2xl bg-[#8b1efc] px-6 py-5"
    >
      <div>
        <h1 className="text-[28px] font-semibold tracking-tight text-white">
          Dashboard
        </h1>
        <p className="mt-0.1 text-[14px] text-white/80">
          Monitor leads, conversations, campaigns, and contacts at a glance.
        </p>
      </div>

      <div className="flex items-center gap-3">
        {/* PROFILE */}
        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setShowProfileMenu((prev) => !prev)}
            aria-haspopup="menu"
            aria-expanded={showProfileMenu}
            className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2.5 transition-colors hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-[13px] font-semibold text-white">
              {initials}
            </div>
            <div className="hidden text-left sm:block">
              <p className="text-[13px] font-medium leading-tight text-white capitalize">
                {displayName}
              </p>
              <p className="text-[11px] leading-tight text-white/70 capitalize">
                {displayRole}
              </p>
            </div>
            <ChevronDown
              size={16}
              strokeWidth={1.8}
              className={`hidden text-white/80 transition-transform sm:block ${
                showProfileMenu ? "rotate-180" : ""
              }`}
            />
          </button>

          {showProfileMenu && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.15 }}
              role="menu"
              className="absolute right-0 top-[calc(100%+8px)] z-50 w-52 overflow-hidden rounded-xl border border-[#e2e8f0] bg-white py-1.5 shadow-lg shadow-black/5"
            >
              <div className="border-b border-[#f1f5f9] px-4 py-2.5">
                <p className="text-[13px] font-medium text-[#0f172a] capitalize">
                  {displayName}
                </p>
                <p className="text-[12px] text-[#94a3b8]">{displayEmail}</p>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                role="menuitem"
                className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-[13px] text-[#dc2626] transition-colors hover:bg-[#fef2f2]"
              >
                <LogOut size={16} strokeWidth={1.8} />
                Log out
              </button>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}