"use client";

import { X, User, Mail, Phone, Building2, Shield, Calendar } from "lucide-react";
import { useMemo, useState } from "react";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function ProfileModal({
  isOpen,
  onClose,
}: ProfileModalProps) {
  const [errors, setErrors] = useState({
    name: "",
    email: "",
    phoneNumber: "",
    companyName: "",
  });

  const [profileData, setProfileData] = useState({
    companyName: "",
    name: "",
    email: "",
    phoneNumber: "",
    role: "Administrator",
    memberSince: "",
  });

  const initials = useMemo(() => {
    const names = profileData.name.trim().split(" ");

    if (names.length === 1) {
      return names[0].charAt(0).toUpperCase();
    }

    return (
      names[0].charAt(0) +
      names[names.length - 1].charAt(0)
    ).toUpperCase();
  }, [profileData.name]);

  const validateField = (
    name: string,
    value: string
  ) => {
    switch (name) {
      case "name":
        if (!value.trim())
          return "Full Name is required";

        if (!/^[A-Za-z ]+$/.test(value))
          return "Only alphabets are allowed";

        if (value.trim().length < 2)
          return "Minimum 2 characters";

        return "";

      case "email":
        if (!value.trim())
          return "Email is required";

        if (
          !/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(
            value
          )
        )
          return "Enter a valid email";

        return "";

      case "phoneNumber":
        if (!value)
          return "Phone Number is required";

        if (!/^\d{10}$/.test(value))
          return "Enter a valid 10-digit number";

        return "";

      case "companyName":
        if (!value.trim())
          return "Company Name is required";

        return "";

      default:
        return "";
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { name, value } = e.target;

    let newValue = value;

    if (name === "phoneNumber") {
      newValue = value.replace(/\D/g, "").slice(0, 10);
    }

    setProfileData((prev) => ({
      ...prev,
      [name]: newValue,
    }));

    setErrors((prev) => ({
      ...prev,
      [name]: validateField(name, newValue),
    }));
  };

  const getAuthToken = () => {
    return (
      sessionStorage.getItem("token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("authToken") ||
      ""
    );
  };

  const authFetch = async (path: string, options: RequestInit) => {
    const token = getAuthToken();
    const res = await fetch(path, {
      ...options,
      headers: {
        ...(options.headers || {}),
        Authorization: token ? `Bearer ${token}` : "",
        "Content-Type": "application/json",
      },
    });
    return res;
  };

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
      setProfileData({
        name: d.name ?? "",
        email: d.email ?? "",
        phoneNumber: d.phoneNumber ?? "",
        companyName: d.companyName ?? "",
        role: d.role ?? "",
        memberSince: d.memberSince ?? "",
      });
    } catch {
      // ignore
    }
  };

  // load on open
  // (keep existing UI; only connect data)
  const [isLoaded, setIsLoaded] = useState(false);

  if (isOpen && !isLoaded) {
    // Trigger once when opening (client component)
    fetchProfile().finally(() => setIsLoaded(true));
  }


  const handleSave = async () => {
    const newErrors = {
      name: validateField("name", profileData.name),
      email: validateField("email", profileData.email),
      phoneNumber: validateField(
        "phoneNumber",
        profileData.phoneNumber
      ),
      companyName: validateField(
        "companyName",
        profileData.companyName
      ),
    };

    setErrors(newErrors);

    if (
      Object.values(newErrors).every(
        (value) => value === ""
      )
    ) {
      console.log(profileData);

      try {
        const token = getAuthToken();
        if (!token) return;

        const res = await fetch("/api/profile", {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: profileData.name,
            email: profileData.email,
            mobile: profileData.phoneNumber,
            companyName: profileData.companyName,
          }),
        });

        if (!res.ok) return;

        await fetchProfile();
      } catch {
        // ignore
      }

      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Blur Background */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-white/10 backdrop-blur-md z-40"
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
        <div className="w-full max-w-5xl rounded-3xl overflow-hidden bg-white shadow-2xl">

          {/* Header */}

          <div className="bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 px-10 py-8 relative">

            <button
              onClick={onClose}
              className="absolute right-6 top-6 bg-white/20 hover:bg-white/30 transition rounded-full p-2 text-white"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-6">

              <div className="h-24 w-24 rounded-full bg-white flex items-center justify-center text-3xl font-bold text-violet-700 shadow-lg">
                {initials}
              </div>

              <div>

                <h2 className="text-3xl font-bold text-white">
                  {profileData.name}
                </h2>

                <p className="text-violet-100 mt-1">
                  {profileData.email}
                </p>

                <div className="mt-4 inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-2 text-sm font-medium text-white">
                  <Shield size={16} />
                  {profileData.role}
                </div>

              </div>

            </div>

          </div>

          {/* Body */}

          <div className="p-8">

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

              {/* Personal Information */}

              <div className="rounded-2xl border border-slate-200 p-6">

                <h3 className="text-lg font-semibold text-slate-800 mb-6">
                  Personal Information
                </h3>

                {/* Full Name */}

                <div className="mb-5">

                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                    <User size={16} />
                    Full Name
                  </label>

                  <input
                    name="name"
                    value={profileData.name}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                  />

                  {errors.name && (
                    <p className="mt-1 text-sm text-red-500">
                      {errors.name}
                    </p>
                  )}

                </div>

                {/* Email */}

                <div className="mb-5">

                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Mail size={16} />
                    Email
                  </label>

                  <input
                    type="email"
                    name="email"
                    value={profileData.email}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                  />

                  {errors.email && (
                    <p className="mt-1 text-sm text-red-500">
                      {errors.email}
                    </p>
                  )}
                </div>
                                {/* Phone Number */}

                <div className="mb-5">

                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Phone size={16} />
                    Phone Number
                  </label>

                  <input
                    type="tel"
                    name="phoneNumber"
                    value={profileData.phoneNumber}
                    onChange={handleChange}
                    maxLength={10}
                    className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                  />

                  {errors.phoneNumber && (
                    <p className="mt-1 text-sm text-red-500">
                      {errors.phoneNumber}
                    </p>
                  )}

                </div>

              </div>

              {/* Account Information */}

              <div className="rounded-2xl border border-slate-200 p-6">

                <h3 className="text-lg font-semibold text-slate-800 mb-6">
                  Account Information
                </h3>

                {/* Company */}

                <div className="mb-5">

                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Building2 size={16} />
                    Company Name
                  </label>

                  <input
                    type="text"
                    name="companyName"
                    value={profileData.companyName}
                    onChange={handleChange}
                    className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-200"
                  />

                  {errors.companyName && (
                    <p className="mt-1 text-sm text-red-500">
                      {errors.companyName}
                    </p>
                  )}

                </div>

                {/* Role */}

                <div className="mb-5">

                  <label className="mb-2 text-sm font-medium text-slate-700">
                    Role
                  </label>

                  <div className="rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 flex items-center gap-2">
                    <Shield
                      size={18}
                      className="text-violet-600"
                    />

                    <span className="font-medium text-violet-700">
                      {profileData.role}
                    </span>
                  </div>

                </div>

                {/* Member Since */}

                <div>

                  <label className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
                    <Calendar size={16} />
                    Member Since
                  </label>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-600">
                    {profileData.memberSince}
                  </div>

                </div>

              </div>

            </div>

            {/* Buttons */}

            <div className="mt-10 flex justify-end gap-4 border-t pt-6">

              <button
                onClick={onClose}
                className="rounded-xl border border-slate-300 px-6 py-3 font-medium text-slate-700 transition hover:bg-slate-100"
              >
                Cancel
              </button>

              <button
                onClick={handleSave}
                className="rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 px-7 py-3 font-medium text-white shadow-lg transition hover:scale-[1.02] hover:shadow-xl"
              >
                Save Changes
              </button>

            </div>

          </div>

        </div>

      </div>

    </>
  );

}