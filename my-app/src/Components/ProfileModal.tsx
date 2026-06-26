"use client";

import {
  Calendar,
  Mail,
  Phone,
  Shield,
  User,
  X,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSidebar } from "@/Components/SideBar";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProfileUpdated?: (profile: { name: string; role: string }) => void;
}

interface ProfileData {
  companyName: string;
  name: string;
  email: string;
  phoneNumber: string;
  role: string;
  memberSince: string;
}

type EditableFieldName = "name" | "email" | "phoneNumber";

const emptyProfileData: ProfileData = {
  companyName: "",
  name: "",
  email: "",
  phoneNumber: "",
  role: "Administrator",
  memberSince: "",
};

const getAuthToken = () => {
  return (
    sessionStorage.getItem("token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("authToken") ||
    ""
  );
};

export default function ProfileModal({
  isOpen,
  onClose,
}: ProfileModalProps) {
  const [profileData, setProfileData] =
    useState<ProfileData>(emptyProfileData);
  const { isCollapsed } = useSidebar();
  const modalOffsetClass = isCollapsed ? "md:left-20" : "md:left-64";

  const initials = useMemo(() => {
    const names = profileData.name.trim().split(" ").filter(Boolean);

    if (names.length === 0) return "A";
    if (names.length === 1) return names[0].charAt(0).toUpperCase();

    return (
      names[0].charAt(0) + names[names.length - 1].charAt(0)
    ).toUpperCase();
  }, [profileData.name]);

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;

    const fetchProfile = async () => {
      try {
        const token = getAuthToken();
        if (!token) return;

        const res = await fetch("/api/profile", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;

        const json = await res.json();
        const d = json?.data || {};
        const nextProfileData = {
          name: d.name ?? "",
          email: d.email ?? "",
          phoneNumber: d.phoneNumber ?? "",
          companyName: d.companyName ?? "",
          role: d.role ?? "Administrator",
          memberSince: d.memberSince ?? "",
        };

        if (!isMounted) return;

        setProfileData(nextProfileData);
      } catch {
        // Keep the modal usable if profile refresh fails.
      }
    };

    fetchProfile();

    return () => {
      isMounted = false;
    };
  }, [isOpen]);

  const handleClose = () => {
    onClose();
  };

  if (!isOpen) return null;

  const editableFields: Array<{
    name: EditableFieldName;
    label: string;
    type: string;
    icon: LucideIcon;
  }> = [
    {
      name: "name",
      label: "Full Name",
      type: "text",
      icon: User,
    },
    {
      name: "email",
      label: "Email Address",
      type: "email",
      icon: Mail,
    },
    {
      name: "phoneNumber",
      label: "Phone Number",
      type: "tel",
      icon: Phone,
    },
  ];

  const renderEditableField = (
    field: (typeof editableFields)[number]
  ) => {
    const Icon = field.icon;

    return (
      <div>
        <label className="mb-2 block text-sm font-semibold text-slate-950">
          {field.label}
        </label>

        <div
          className="relative flex min-h-16 overflow-hidden rounded-lg border border-slate-200 bg-white"
        >
          <Icon
            size={22}
            strokeWidth={2.2}
            className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-violet-700"
          />

          <input
            type={field.type}
            name={field.name}
            value={profileData[field.name]}
            readOnly
            className="min-w-0 flex-1 cursor-default bg-white py-4 pl-14 pr-4 text-base font-medium text-slate-950 outline-none"
          />
        </div>
      </div>
    );
  };

  return (
    <>
      <div
        onClick={handleClose}
        className={`fixed inset-y-0 right-0 left-0 z-40 bg-white/30 backdrop-blur-lg ${modalOffsetClass}`}
      />

      <div
        className={`fixed inset-y-0 right-0 left-0 z-50 flex items-center justify-center p-4 ${modalOffsetClass}`}
      >
        <div className="w-[min(94vw,980px)] overflow-hidden rounded-lg bg-white shadow-2xl ring-1 ring-slate-200/80">
          <div className="relative overflow-hidden bg-gradient-to-r from-violet-700 via-purple-700 to-indigo-700 px-6 py-5 sm:px-8">
            <div className="pointer-events-none absolute inset-x-0 bottom-0 hidden h-20 opacity-20 lg:block">
              <div className="absolute right-0 top-3 h-px w-1/2 rotate-[-8deg] bg-white/40" />
              <div className="absolute right-0 top-9 h-px w-3/5 rotate-[-8deg] bg-white/30" />
              <div className="absolute right-0 top-16 h-px w-1/2 rotate-[-8deg] bg-white/25" />
              <div className="absolute right-0 top-20 h-px w-2/5 rotate-[-8deg] bg-white/20" />
            </div>

            <div className="absolute right-5 top-5 z-20">
              <button
                type="button"
                onClick={handleClose}
                aria-label="Close profile"
                className="p-2 text-white/80 transition hover:text-white"
              >
                <X size={22} />
              </button>
            </div>

            <div className="relative flex items-center gap-5 pr-14 sm:gap-6">
              <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-full bg-white text-4xl font-bold text-violet-700 shadow-xl sm:h-24 sm:w-24">
                {initials}
              </div>

              <div className="min-w-0">
                <h2 className="truncate text-3xl font-bold text-white sm:text-4xl">
                  {profileData.name || "Admin"}
                </h2>

                <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-semibold text-white backdrop-blur">
                  <Shield size={18} />
                  {profileData.role || "Administrator"}
                </div>
              </div>
            </div>
          </div>

          <div className="px-6 py-5 sm:px-8">
            <div className="text-center">
              <h3 className="text-xl font-bold text-slate-950">
                Profile Information
              </h3>
              <div className="mx-auto mt-2 h-1 w-28 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600" />
              <p className="mt-2 text-sm text-slate-500">
                Manage your personal details and contact information.
              </p>
            </div>

            <div className="mt-7 grid gap-6 lg:grid-cols-[1fr_auto_1fr] lg:gap-8">
              <div className="space-y-5">
                {renderEditableField(editableFields[0])}
                {renderEditableField(editableFields[1])}
              </div>

              <div className="hidden w-px bg-slate-200 lg:block" />

              <div className="space-y-5">
                {renderEditableField(editableFields[2])}

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-950">
                    Member Since
                  </label>

                  <div className="relative flex min-h-16 overflow-hidden rounded-lg border border-slate-200 bg-white">
                    <Calendar
                      size={22}
                      strokeWidth={2.2}
                      className="pointer-events-none absolute left-5 top-1/2 -translate-y-1/2 text-violet-700"
                    />

                    <div className="flex min-w-0 flex-1 items-center py-4 pl-14 pr-12 text-base font-medium text-slate-500">
                      {profileData.memberSince || "Not available"}
                    </div>

                    <div className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-950">
                      <Calendar size={22} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
