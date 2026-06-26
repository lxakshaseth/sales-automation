import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { LogOut, ChevronDown, User } from "lucide-react";
import toast from "react-hot-toast";
import { useRouter } from "next/navigation";
import ProfileModal from "@/Components/ProfileModal";

interface UserType {
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
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [user, setUser] = useState<UserType | null>(null);
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
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node)
      ) {
        setShowProfileMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () =>
      document.removeEventListener("mousedown", handleClickOutside);
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
    <>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mb-8 flex items-start justify-between gap-6 px-2 pb-4 border-b border-slate-200"
      >
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-500">
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
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-600 text-[14px] font-semibold text-white">
                {initials}
              </div>
              <div className="hidden text-left sm:block">
                <p className="text-[14px] font-bold leading-tight text-gray-900 capitalize">
                  {displayName}
                </p>
                <p className="text-[12px] leading-tight text-gray-400 capitalize">
                  {displayRole}
                </p>
              </div>
              <ChevronDown
                size={16}
                strokeWidth={1.8}
                className={`hidden text-gray-500 transition-transform sm:block ${
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
              
                {/* Profile Button — only addition */}
                <button
                  type="button"
                  onClick={() => {
                    setShowProfileModal(true);
                    setShowProfileMenu(false);
                  }}
                  role="menuitem"
                  className="flex w-full items-center gap-2.5 px-4 py-2.5 text-left text-[13px] text-[#0f172a] transition-colors hover:bg-[#f8fafc]"
                >
                  <User size={16} strokeWidth={1.8} />
                  Profile
                </button>

                {/* Logout — exactly same as before */}
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

      {/* Profile Modal — only opens when Profile is clicked */}
      <ProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
      />
    </>
  );
}