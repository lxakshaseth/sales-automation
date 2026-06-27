"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Rocket, Eye, EyeOff } from "lucide-react";

export default function Signin() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setLoading(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success("Login successful");
        sessionStorage.setItem("token", data.token);
        sessionStorage.setItem("user", JSON.stringify(data.data));
        if (rememberMe) {
          localStorage.setItem("savedEmail", formData.email);
          localStorage.setItem("savedPassword", formData.password);
        } else {
          localStorage.removeItem("savedEmail");
          localStorage.removeItem("savedPassword");
        }

        setTimeout(() => {
          router.push("/");
        }, 1000);
      } else {
        toast.error(data.message || "Login failed");
      }
    } catch (error) {
      console.error(error);
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedEmail = localStorage.getItem("savedEmail");
    const savedPassword = localStorage.getItem("savedPassword");

    if (savedEmail && savedPassword) {
      setFormData((prev) => ({
        ...prev,
        email: savedEmail,
        password: savedPassword,
      }));

      setRememberMe(true);
    }
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-linear-to-br from-violet-50 via-white to-indigo-100 relative overflow-hidden">
      <div className="absolute top-20 left-20 h-72 w-72 rounded-full bg-violet-300/30 blur-3xl"></div>

      <div className="absolute bottom-20 right-20 h-72 w-72 rounded-full bg-indigo-300/30 blur-3xl"></div>

      <div className="relative z-10 flex flex-col items-center w-full max-w-6xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#7C3AED] text-white shadow-lg">
            <Rocket className="h-7 w-7" />
          </div>

          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Sales Automation
            </h1>
            <p className="text-md text-slate-500">CRM & Lead Management</p>
          </div>
        </div>

        <div className="w-full max-w-5xl rounded-2xl overflow-hidden bg-white/90 backdrop-blur-md shadow-2xl border border-white/20">
          <div className="grid md:grid-cols-[1.1fr_0.9fr]">
            {/* Left Side - Form */}
            <div className="p-12 flex flex-col justify-center">
              <h2 className="text-2xl font-bold text-center text-slate-900 mb-8">
                Sign In
              </h2>

              <form onSubmit={handleSubmit}>
                <input
                  type="email"
                  name="email"
                  required
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={loading}
                  className="w-full border border-gray-300 rounded-lg p-3 mb-4 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <div className="relative mb-6">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    required
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleChange}
                    disabled={loading}
                    className="w-full border border-gray-300 rounded-lg p-3 mb-6 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />

                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/3 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword ? <EyeOff></EyeOff> : <Eye></Eye>}
                  </button>
                </div>

                <div className="flex items-center justify-between mb-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-violet-600 focus:ring-violet-500"
                    />
                    <span className="text-sm text-slate-600">Remember me</span>
                  </label>

                  <button
                    type="button"
                    className="text-sm text-violet-600 hover:underline"
                  >
                    {/* Forgot Password? */}
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#7C3AED] text-white py-3 rounded-lg font-semibold hover:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Signing In..." : "Sign In"}
                </button>
              </form>

              <p className="text-center text-sm text-slate-600 mt-6">
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => router.push("/sign-up")}
                  className="text-violet-600 font-semibold hover:underline"
                >
                  Sign Up
                </button>
              </p>
            </div>

            {/* Right Side - Premium Welcome */}
            <div className="hidden md:flex relative overflow-hidden flex-col justify-center bg-linear-to-br from-violet-700 via-violet-600 to-indigo-700 text-white p-12">
              {/* Decorative Blobs */}
              <div className="absolute -top-20 -right-20 h-64 w-64 rounded-full bg-white/10 blur-3xl"></div>
              <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-indigo-300/20 blur-3xl"></div>

              <div className="relative z-10">
                <span className="inline-flex items-center rounded-full bg-white/10 px-4 py-1 text-sm backdrop-blur-md border border-white/20">
                  🚀 Smart CRM Platform
                </span>

                <h2 className="mt-6 text-5xl font-bold leading-tight">
                  Welcome <br />
                  Back
                </h2>

                {/* Features */}
                <div className="mt-10 space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <span>Lead Management & Tracking</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <span>Bulk CSV Lead Import</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <span>Campaign Automation</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <span>Real-time Analytics</span>
                  </div>
                </div>

                {/* Stats Cards */}
                <div className="mt-10 grid grid-cols-2 gap-4">
                  <div className="rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 p-4">
                    <p className="text-violet-200 text-sm">Leads Managed</p>
                    <h3 className="text-2xl font-bold">10K+</h3>
                  </div>

                  <div className="rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 p-4">
                    <p className="text-violet-200 text-sm">Campaigns</p>
                    <h3 className="text-2xl font-bold">500+</h3>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}