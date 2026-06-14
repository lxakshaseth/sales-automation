"use client";
import React, { useState } from "react";
import toast from "react-hot-toast";
import { Rocket } from "lucide-react";
import { useRouter } from "next/navigation";


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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();


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

      const data = await response.json();

      if (response.ok) {
        toast.success("Registration successful");
        // console.log(data);

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
      }

      else {
        toast.error(data.message || "Registration failed");
      }
    } catch (error) {
      console.error(error);
      toast.error("Something went wrong");
    }
    finally {
      setLoading(false);
    }

  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-linear-to-br from-violet-50 via-white to-indigo-100 relative overflow-hidden">


      <div className="absolute top-20 left-20 h-72 w-72 rounded-full bg-violet-300/30 blur-3xl"></div>

      <div className="absolute bottom-20 right-20 h-72 w-72 rounded-full bg-indigo-300/30 blur-3xl"></div>


      <div className="relative z-10 flex flex-col items-center w-full max-w-lg">


        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#7C3AED] text-white shadow-lg">
            <Rocket className="h-7 w-7" />
          </div>

          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Sales Automation
            </h1>
            <p className="text-sm text-slate-500">
              CRM & Lead Management
            </p>
          </div>
        </div>


        <div className="w-full max-w-2xl rounded-2xl bg-white/90 backdrop-blur-md p-8 shadow-2xl border border-white/20">
          <h2 className="text-2xl font-bold text-center text-slate-900 mb-6">
            Sign Up
          </h2>

          <form onSubmit={handleSubmit}>
            <input
              type="text"
              name="name"
              required
              placeholder="Name"
              value={formData.name}
              onChange={handleChange}
              disabled={loading}
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
            />

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
            <input
              type="tel"
              name="mobile"
              required
              maxLength={10}

              placeholder="Mobile No"
              value={formData.mobile}
              onChange={handleChange}
              disabled={loading}
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
            />

            <input
              type="password"
              name="password"
              required
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
              className="w-full border border-gray-300 rounded-lg p-3 mb-4 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
            />

            <input
              type="password"
              name="confirmPassword"
              required
              placeholder="Confirm Password"
              value={formData.confirmPassword}
              onChange={handleChange}
              disabled={loading}
              className="w-full border border-gray-300 rounded-lg p-3 mb-6 text-black focus:outline-none focus:ring-2 focus:ring-violet-500"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#7C3AED] text-white py-3 rounded-lg font-semibold hover:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Registering..." : "Register"}
            </button>
          </form>
          <div>
              <p className="text-center text-sm text-slate-600  mt-6">
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
  );
}