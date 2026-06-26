"use client";

import { LogOut, User } from "lucide-react";
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
  const [isUserLoaded, setIsUserLoaded] = useState(false);

  const router = useRouter();

  const handleLogout = () => {
    sessionStorage.removeItem("token");
    toast.success("Logout Successfully");
    router.push("/sign-in");
  };

  useEffect(() => {
    if (isUserLoaded) return;
    const fetchProfile = async () => {
      const token = sessionStorage.getItem("token") || localStorage.getItem("token") || localStorage.getItem("authToken");
      if (!token) return;
      try {
        const res = await fetch("/api/profile", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const json = await res.json();
        const d = json?.data || {};
        setUser({
          name: d.name || "",
          role: d.role || "",
        });
      } catch {
        // ignore
      } finally {
        setIsUserLoaded(true);
      }
    };
    fetchProfile();
  }, [isUserLoaded]);

  const initials = useMemo(() => {
    const names = user.name.trim().split(" ").filter(Boolean);
    if (names.length === 0) return "";
    if (names.length === 1) return names[0].charAt(0).toUpperCase();
    return (
      names[0].charAt(0).toUpperCase() +
      names[names.length - 1].charAt(0).toUpperCase()
    );
  }, [user.name]);

  const firstName = useMemo(() => {
    return user.name.trim().split(" ").filter(Boolean)[0] || "";
  }, [user.name]);

  const lastName = useMemo(() => {
    const names = user.name.trim().split(" ").filter(Boolean);
    return names.length > 1 ? names[names.length - 1] : "";
  }, [user.name]);

  return (
    <>
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
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="flex items-center gap-2"
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                {initials || "A"}
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-sm font-semibold">
                  {firstName || "Admin"}
                </p>
                <p className="text-xs text-slate-500">
                  {lastName || "Administrator"}
                </p>
              </div>
            </button>

            {showProfileMenu && (
              <div className="absolute right-0 top-14 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
                <button
                  onClick={() => {
                    setShowProfileModal(true);
                    setShowProfileMenu(false);
                  }}
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

      <ProfileModal
        isOpen={showProfileModal}
        onClose={() => setShowProfileModal(false)}
      />
    </>
  );
}