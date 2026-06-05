"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import {
  ArrowRight,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  Circle,
  Eye,
  EyeOff,
  Lock,
  Mail,
  MessageSquare,
  Rocket,
  User,
} from "lucide-react";

type AuthMode = "sign-in" | "sign-up";

interface AuthPageProps {
  mode: AuthMode;
}

const trustIndicators = [
  "No Credit Card Required",
  "Setup in Under 2 Minutes",
  "Secure Cloud Workspace",
];

const stats = [
  { label: "Total Leads", value: "1,284" },
  { label: "Active Campaigns", value: "42" },
  { label: "Conversion Rate", value: "18.7%" },
  { label: "Monthly Revenue", value: "₹8.4L" },
];

const pipeline = [
  { label: "New Leads", value: 24, width: "92%" },
  { label: "Qualified", value: 18, width: "76%" },
  { label: "Proposal", value: 11, width: "58%" },
  { label: "Negotiation", value: 6, width: "42%" },
  { label: "Won Deals", value: 4, width: "30%" },
];

const activities = [
  "Rahul Sharma created a new lead",
  'Campaign "Summer Offer" launched',
  "Proposal sent to Acme Pvt Ltd",
  "Follow-up task completed",
  "Lead status changed to Qualified",
];

export default function AuthPage({ mode }: AuthPageProps) {
  const router = useRouter();
  const isSignUp = mode === "sign-up";
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const copy = useMemo(
    () => ({
      title: isSignUp ? "Create your workspace" : "Welcome back",
      subtitle: isSignUp
        ? "Manage leads, contacts, campaigns, pipelines, and customer conversations from one place."
        : "Sign in to continue managing your leads, deals, and campaigns.",
      button: isSignUp ? "Create Workspace" : "Sign In",
      switchText: isSignUp
        ? "Already have an account?"
        : "Don't have an account?",
      switchAction: isSignUp ? "Sign In" : "Create Workspace",
      switchHref: isSignUp ? "/sign-in" : "/sign-up",
    }),
    [isSignUp]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!form.email.trim() || !form.password.trim() || (isSignUp && (!form.name.trim() || !form.confirmPassword.trim()))) {
      toast.error("Please fill all required fields");
      return;
    }

    if (isSignUp && form.password !== form.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`/api/auth/${isSignUp ? "register" : "login"}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          isSignUp
            ? {
                name: form.name.trim(),
                email: form.email.trim(),
                password: form.password,
              }
            : {
                email: form.email.trim(),
                password: form.password,
              }
        ),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.message || "Authentication failed");
      }

      if (rememberMe) {
        localStorage.setItem("salesAutomationToken", result.token);
      } else {
        sessionStorage.setItem("salesAutomationToken", result.token);
      }

      toast.success(isSignUp ? "Account created successfully" : "Signed in successfully");
      router.push("/");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Something went wrong");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#F8FAFC] px-4 py-6 text-[#0F172A] sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-7xl items-center justify-center">
        <section className="grid w-full overflow-hidden rounded-2xl border border-[#E2E8F0] bg-white shadow-[0_24px_70px_rgba(15,23,42,0.08)] lg:min-h-180 lg:grid-cols-[45%_55%]">
          <div className="flex flex-col justify-center px-6 py-8 sm:px-10 lg:px-14 xl:px-16">
            <Link
              href="/"
              className="mb-9 flex w-fit items-center gap-3 text-slate-900"
              aria-label="Go to dashboard"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#7C3AED] text-white shadow-sm">
                <Rocket className="h-5 w-5" />
              </span>
              <span className="text-lg font-semibold leading-tight tracking-tight">
                Sales
                <span className="block text-[#7C3AED]">Automation</span>
              </span>
            </Link>

            <h1 className="text-3xl font-semibold tracking-tight text-[#0F172A] sm:text-4xl">
              {copy.title}
            </h1>
            <p className="mt-4 max-w-md text-sm leading-6 text-slate-600 sm:text-base">
              {copy.subtitle}
            </p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-4">
              {isSignUp && (
                <label className="block">
                  <span className="sr-only">Full name</span>
                  <span className="relative block">
                    <User className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                    <input
                      value={form.name}
                      onChange={(event) =>
                        setForm((current) => ({ ...current, name: event.target.value }))
                      }
                      type="text"
                      autoComplete="name"
                      placeholder="Full Name"
                      className="h-13 w-full rounded-2xl border border-[#E2E8F0] bg-white pl-12 pr-4 text-sm text-[#0F172A] outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-[#7C3AED] focus:ring-4 focus:ring-violet-100"
                    />
                  </span>
                </label>
              )}

              <label className="block">
                <span className="sr-only">Email</span>
                <span className="relative block">
                  <Mail className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                  <input
                    value={form.email}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, email: event.target.value }))
                    }
                    type="email"
                    autoComplete="email"
                    placeholder="Work Email"
                    className="h-13 w-full rounded-2xl border border-[#E2E8F0] bg-white pl-12 pr-4 text-sm text-[#0F172A] outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-[#7C3AED] focus:ring-4 focus:ring-violet-100"
                  />
                </span>
              </label>

              <label className="block">
                <span className="sr-only">Password</span>
                <span className="relative block">
                  <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                  <input
                    value={form.password}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, password: event.target.value }))
                    }
                    type={showPassword ? "text" : "password"}
                    autoComplete={isSignUp ? "new-password" : "current-password"}
                    placeholder="Password"
                    className="h-13 w-full rounded-2xl border border-[#E2E8F0] bg-white pl-12 pr-12 text-sm text-[#0F172A] outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-[#7C3AED] focus:ring-4 focus:ring-violet-100"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 rounded-lg p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </span>
              </label>

              {isSignUp && (
                <label className="block">
                  <span className="sr-only">Confirm password</span>
                  <span className="relative block">
                    <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-slate-400" />
                    <input
                      value={form.confirmPassword}
                      onChange={(event) =>
                        setForm((current) => ({ ...current, confirmPassword: event.target.value }))
                      }
                      type={showPassword ? "text" : "password"}
                      autoComplete="new-password"
                      placeholder="Confirm Password"
                      className="h-[52px] w-full rounded-2xl border border-[#E2E8F0] bg-white pl-12 pr-4 text-sm text-[#0F172A] outline-none transition placeholder:text-slate-400 hover:border-slate-300 focus:border-[#7C3AED] focus:ring-4 focus:ring-violet-100"
                    />
                  </span>
                </label>
              )}

              <div className="flex flex-wrap items-center justify-between gap-3 text-sm">
                <label className="flex items-center gap-2 text-slate-600">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(event) => setRememberMe(event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-[#7C3AED] focus:ring-[#7C3AED]"
                  />
                  {isSignUp ? "Keep me signed in" : "Remember Me"}
                </label>
                {!isSignUp && (
                  <Link href="/sign-up" className="font-medium text-[#7C3AED] transition hover:text-violet-700">
                    Forgot password?
                  </Link>
                )}
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="group flex h-[52px] w-full items-center justify-center gap-2 rounded-2xl bg-[#7C3AED] px-5 text-sm font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-violet-700 hover:shadow-md disabled:translate-y-0 disabled:opacity-70"
              >
                {isSubmitting ? "Please wait" : copy.button}
                <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              </button>

              <div className="flex items-center gap-4 py-1 text-xs font-medium uppercase tracking-[0.16em] text-slate-400">
                <span className="h-px flex-1 bg-[#E2E8F0]" />
                OR
                <span className="h-px flex-1 bg-[#E2E8F0]" />
              </div>

              <button
                type="button"
                className="flex h-[52px] w-full items-center justify-center gap-3 rounded-2xl border border-[#E2E8F0] bg-white px-5 text-sm font-semibold text-[#0F172A] transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-sm"
              >
                <span className="flex h-5 w-5 items-center justify-center rounded-full border border-slate-300 text-[11px] font-bold text-[#7C3AED]">
                  G
                </span>
                Continue with Google
              </button>
            </form>

            {isSignUp && (
              <div className="mt-6 grid gap-2 text-sm text-slate-600 sm:grid-cols-3 sm:gap-3">
                {trustIndicators.map((item) => (
                  <div key={item} className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-7 text-center text-sm text-slate-500">
              {copy.switchText}{" "}
              <Link href={copy.switchHref} className="font-semibold text-[#7C3AED] transition hover:text-violet-700">
                {copy.switchAction}
              </Link>
            </div>
          </div>

          <aside className="hidden border-l border-[#E2E8F0] bg-[#F8FAFC] p-8 lg:block xl:p-10">
            <div className="h-full rounded-2xl border border-[#E2E8F0] bg-white p-6 shadow-[0_16px_45px_rgba(15,23,42,0.07)]">
              <div className="mb-6 flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-500">CRM Workspace</p>
                  <h2 className="mt-1 text-2xl font-semibold tracking-tight text-[#0F172A]">
                    Sales overview
                  </h2>
                </div>
                <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" />
                  Workspace Ready
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {stats.map((item) => (
                  <div key={item.label} className="rounded-2xl border border-[#E2E8F0] bg-white p-4 shadow-sm">
                    <p className="text-xs font-medium text-slate-500">{item.label}</p>
                    <p className="mt-2 text-2xl font-semibold tracking-tight text-[#0F172A]">{item.value}</p>
                  </div>
                ))}
              </div>

              <div className="mt-5 grid gap-5 xl:grid-cols-[1fr_0.95fr]">
                <section className="rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm">
                  <div className="mb-5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <BriefcaseBusiness className="h-4 w-4 text-[#7C3AED]" />
                      <h3 className="text-sm font-semibold text-[#0F172A]">Pipeline Preview</h3>
                    </div>
                    <span className="text-xs font-medium text-slate-500">This month</span>
                  </div>

                  <div className="space-y-4">
                    {pipeline.map((item) => (
                      <div key={item.label}>
                        <div className="mb-2 flex items-center justify-between text-sm">
                          <span className="font-medium text-slate-600">{item.label}</span>
                          <span className="font-semibold text-[#0F172A]">{item.value}</span>
                        </div>
                        <div className="h-2 rounded-full bg-slate-100">
                          <div
                            className="h-2 rounded-full bg-[#7C3AED]"
                            style={{ width: item.width }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm">
                  <div className="mb-5 flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-[#7C3AED]" />
                    <h3 className="text-sm font-semibold text-[#0F172A]">Recent Activities</h3>
                  </div>

                  <div className="space-y-4">
                    {activities.map((item) => (
                      <div key={item} className="flex gap-3">
                        <Circle className="mt-1 h-2.5 w-2.5 shrink-0 fill-[#7C3AED] text-[#7C3AED]" />
                        <p className="text-sm leading-5 text-slate-600">{item}</p>
                      </div>
                    ))}
                  </div>
                </section>
              </div>

              <div className="mt-5 rounded-2xl border border-[#E2E8F0] bg-white p-5 shadow-sm">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-[#7C3AED]" />
                    <h3 className="text-sm font-semibold text-[#0F172A]">Campaign performance</h3>
                  </div>
                  <span className="text-xs font-medium text-emerald-700">+12.4%</span>
                </div>
                <div className="grid h-28 grid-cols-12 items-end gap-2">
                  {[44, 58, 38, 72, 66, 80, 54, 88, 62, 76, 92, 84].map((height, index) => (
                    <div
                      key={`${height}-${index}`}
                      className="rounded-t-lg bg-violet-100"
                      style={{ height: `${height}%` }}
                    >
                      <div className="h-full rounded-t-lg bg-[#7C3AED]/80" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
