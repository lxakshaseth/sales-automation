"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { Rocket, Eye, EyeOff } from "lucide-react";

// Shadcn UI Components Imports
import { Button } from "@/Components/ui/button";
import { Input } from "@/Components/ui/input";
import { Label } from "@/Components/ui/label";
import { Card, CardContent } from "@/Components/ui/card";
import { Checkbox } from "@/Components/ui/checkbox";

export default function Signin() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem("token");
    if (token) {
      router.replace("/Dashboard");
    } else {
      setChecking(false);
    }
  }, [router]);

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
          router.push("/Dashboard");
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

  if (checking) return null;

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-linear-to-br from-violet-50 via-white to-indigo-100 relative overflow-hidden">
      {/* Background Decoratives */}
      <div className="absolute top-20 left-20 h-72 w-72 rounded-full bg-violet-300/30 blur-3xl"></div>
      <div className="absolute bottom-20 right-20 h-72 w-72 rounded-full bg-indigo-300/30 blur-3xl"></div>

      <div className="relative z-10 flex flex-col items-center w-full max-w-6xl">
        {/* Header App Brand */}
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

        {/* Main Interface Wrapper Container */}
        <Card className="w-full max-w-5xl rounded-2xl overflow-hidden bg-white/90 backdrop-blur-md shadow-2xl border border-white/20">
          <CardContent className="p-0 grid md:grid-cols-[1.1fr_0.9fr]">
            
            {/* Left Portion - Actionable Auth Form */}
            <div className="p-12 flex flex-col justify-center">
              <h2 className="text-2xl font-bold text-center text-slate-900 mb-8">
                Sign In
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    name="email"
                    required
                    placeholder="name@example.com"
                    value={formData.email}
                    onChange={handleChange}
                    disabled={loading}
                    className="w-full border-gray-300 text-black focus-visible:ring-violet-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      name="password"
                      required
                      placeholder="Enter your password"
                      value={formData.password}
                      onChange={handleChange}
                      disabled={loading}
                      className="w-full border-gray-300 text-black pr-10 focus-visible:ring-violet-500"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-1 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 hover:bg-transparent"
                    >
                      {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                    </Button>
                  </div>
                </div>

                {/* Account Context Options */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="rememberMe"
                      checked={rememberMe}
                      onCheckedChange={(checked) => setRememberMe(!!checked)}
                      className="border-gray-300 data-[state=checked]:bg-[#7C3AED] data-[state=checked]:border-[#7C3AED]"
                    />
                    <Label
                      htmlFor="rememberMe"
                      className="text-sm font-medium leading-none text-slate-600 cursor-pointer select-none"
                    >
                      Remember me
                    </Label>
                  </div>

                  <Button
                    type="button"
                    variant="link"
                    className="text-sm text-violet-600 p-0 h-auto hover:underline"
                  >
                    {/* Forgot Password Space */}
                  </Button>
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-[#7C3AED] hover:bg-violet-700 text-white font-semibold transition-all py-6 mt-4"
                >
                  {loading ? "Signing In..." : "Sign In"}
                </Button>
              </form>

              <p className="text-center text-sm text-slate-600 mt-6">
                Don't have an account?{" "}
                <Button
                  type="button"
                  variant="link"
                  onClick={() => router.push("/sign-up")}
                  className="text-violet-600 font-semibold p-0 h-auto hover:underline"
                >
                  Sign Up
                </Button>
              </p>
            </div>

            {/* Right Portion - Platform Marketing Display */}
            <div className="hidden md:flex relative overflow-hidden flex-col justify-center bg-linear-to-br from-violet-700 via-violet-600 to-indigo-700 text-white p-12">
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

          </CardContent>
        </Card>
      </div>
    </div>
  );
}