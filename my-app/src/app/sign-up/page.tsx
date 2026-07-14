"use client";
import React, { useState } from "react";
import toast from "react-hot-toast";
import { Rocket, Eye, EyeOff } from "lucide-react";
import { useRouter } from "next/navigation";
import PasswordRequirementChecklist from "@/Components/auth/PasswordRequirementChecklist";
import { getPasswordValidationError } from "@/lib/passwordValidation";
import { readApiResponse } from "@/services/api";

type RegisterResponse = {
  success?: boolean;
  message?: string;
};

export default function Signup() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    mobile: "",
    password: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const passwordValidationError = getPasswordValidationError(
    formData.password,
  );
  const isPasswordValid = !passwordValidationError;
  const shouldShowPasswordError =
    formData.password.length > 0 && Boolean(passwordValidationError);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (passwordValidationError) {
      toast.error(passwordValidationError);
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    if (!/^[0-9]{10}$/.test(formData.mobile)) {
      toast.error("Please enter a valid 10-digit mobile number");
      return;
    }
    setLoading(true);

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: formData.name.trim(),
          email: formData.email.trim(),
          mobile: formData.mobile.trim(),
          password: formData.password,
        }),
      });

      const data = await readApiResponse<RegisterResponse>(
        response,
        "Registration failed",
      );

      if (response.ok) {
        toast.success("Registration successful");
        setFormData({
          name: "",
          email: "",
          mobile: "",
          password: "",
          confirmPassword: "",
        });
        setTimeout(() => {
          router.push("/sign-in");
        }, 1500);
      } else {
        toast.error(data.message || "Registration failed");
      }
    } catch (error) {
      console.error(error);
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

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
          <div className="grid md:grid-cols-[0.9fr_1.1fr]">
            <div className="hidden md:flex relative overflow-hidden flex-col bg-linear-to-br from-violet-700 via-violet-600 to-indigo-700 p-10">
              <div className="absolute -top-20 -right-20 h-64 w-64 rounded-full bg-white/10 blur-3xl"></div>
              <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-indigo-300/20 blur-3xl"></div>

              <div className="relative z-10 flex flex-col h-full">
                {/* Smart CRM */}
                <span className="inline-flex w-fit items-center rounded-full bg-white/10 px-4 py-1 text-sm backdrop-blur-md border border-white/20 text-white">
                  🚀 Smart CRM Platform
                </span>

                <h2 className="mt-6 text-5xl font-bold leading-tight text-white">
                  Create <br />
                  Account
                </h2>

                <div className="mt-10 space-y-4 text-lg text-white">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <p>Easy Account Setup</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <p>Secure Authentication</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <p>Access to Dashboard</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="h-2 w-2 rounded-full bg-green-400"></div>
                    <p>Start Managing Leads</p>
                  </div>
                </div>
              </div>

              {/* Bottom Cards */}
              <div className="mt-10 grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 p-4">
                  <p className="text-violet-200 text-sm">Leads Managed</p>
                  <h3 className="text-2xl font-bold text-white">10K+</h3>
                </div>

                <div className="rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 p-4">
                  <p className="text-violet-200 text-sm">Campaigns</p>
                  <h3 className="text-2xl font-bold text-white">500+</h3>
                </div>
              </div>
            </div>
            <div className="p-12 flex flex-col justify-center">
              <h2 className="text-2xl font-bold text-center text-slate-900 mb-6">
                Sign Up!
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <input
                  type="text"
                  name="name"
                  required
                  placeholder="Name"
                  value={formData.name}
                  onChange={handleChange}
                  disabled={loading}
                  className="w-full border border-gray-300 rounded-lg p-3 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                />

                <input
                  type="email"
                  name="email"
                  required
                  placeholder="Email"
                  value={formData.email}
                  onChange={handleChange}
                  disabled={loading}
                  className="w-full border border-gray-300 rounded-lg p-3 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                />

                <input
                  type="tel"
                  name="mobile"
                  required
                  maxLength={10}
                  placeholder="Mobile No"
                  value={formData.mobile}
                  onChange={handleChange}
                  disabled={loading}
                  className="w-full border border-gray-300 rounded-lg p-3 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                />

                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    name="password"
                    required
                    aria-label="Password"
                    placeholder="Password"
                    value={formData.password}
                    onChange={handleChange}
                    disabled={loading}
                    aria-invalid={shouldShowPasswordError}
                    aria-describedby="password-requirements"
                    className="w-full border border-gray-300 rounded-lg p-3 pr-12 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                  />
                  <button
                    type="button"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showPassword ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>

                <PasswordRequirementChecklist
                  password={formData.password}
                  className="-mt-2"
                />

                <input
                  type="text"
                  name="confirmPassword"
                  required
                  aria-label="Confirm password"
                  placeholder="Confirm Password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  disabled={loading}
                  className="w-full border border-gray-300 rounded-lg p-3 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
                />

                <button
                  type="submit"
                  disabled={loading || !isPasswordValid}
                  className="w-full bg-[#7C3AED] text-white py-3 rounded-lg font-semibold hover:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed pt-2"
                >
                  {loading ? "Registering..." : "Register"}
                </button>
              </form>
              <div>
                <p className="text-center text-sm text-slate-600 mt-6">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => router.push("/sign-in")}
                    className="text-violet-600 font-semibold hover:underline"
                  >
                    Sign In
                  </button>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
