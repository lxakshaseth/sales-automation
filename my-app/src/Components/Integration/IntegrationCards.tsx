"use client";

import {
  FaWhatsapp,
  FaFacebook,
  FaInstagram,
  FaLinkedin,
  FaArrowRight,
  FaLock,
} from "react-icons/fa";

import { FaXTwitter, FaMessage } from "react-icons/fa6";
import { MdEmail } from "react-icons/md";

export default function IntegrationCards() {
  const integrations = [
    {
      name: "WhatsApp",
      icon: FaWhatsapp,
      status: "Active",
      color: "text-green-600",
      bg: "bg-green-50",
      border: "border-green-200",
      description:
        "Connect WhatsApp campaigns, automate replies and manage customer conversations.",
    },
    {
      name: "Email",
      icon: MdEmail,
      status: "Active",
      color: "text-blue-600",
      bg: "bg-blue-50",
      border: "border-blue-200",
      description:
        "Connect Gmail or Outlook and create automated email workflows.",
    },
    {
      name: "Facebook",
      icon: FaFacebook,
      status: "Coming Soon",
      color: "text-blue-700",
      bg: "bg-blue-50",
      border: "border-blue-200",
      description:
        "Manage Facebook messages and generate leads from campaigns.",
    },
    {
      name: "Instagram",
      icon: FaInstagram,
      status: "Coming Soon",
      color: "text-pink-600",
      bg: "bg-pink-50",
      border: "border-pink-200",
      description:
        "Automate Instagram DMs, comments and engagement workflows.",
    },
    {
      name: "Twitter X",
      icon: FaXTwitter,
      status: "Coming Soon",
      color: "text-slate-700",
      bg: "bg-slate-50",
      border: "border-slate-200",
      description:
        "Track mentions, engage with users and automate outreach.",
    },
    {
      name: "LinkedIn",
      icon: FaLinkedin,
      status: "Coming Soon",
      color: "text-blue-800",
      bg: "bg-blue-50",
      border: "border-blue-200",
      description:
        "Capture B2B leads and automate professional networking.",
    },
    {
      name: "SMS",
      icon: FaMessage,
      status: "Coming Soon",
      color: "text-violet-600",
      bg: "bg-violet-50",
      border: "border-violet-200",
      description:
        "Send targeted SMS campaigns and customer notifications.",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {integrations.map((item, index) => {
        const Icon = item.icon;
        const isActive = item.status === "Active";

        return (
          <div
            key={index}
            className="group bg-white border border-[#e5e7eb] rounded-3xl p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
          >
            {/* Top */}
            <div className="flex items-start justify-between">
              <div
                className={`w-14 h-14 rounded-2xl flex items-center justify-center ${item.bg}`}
              >
                <Icon className={`text-2xl ${item.color}`} />
              </div>

              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  isActive
                    ? "bg-green-100 text-green-700"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                {item.status}
              </span>
            </div>

            {/* Content */}
            <div className="mt-5">
              <h3 className="text-xl font-bold text-[#111827]">
                {item.name}
              </h3>

              <p className="mt-3 text-sm text-[#64748b] leading-relaxed">
                {item.description}
              </p>
            </div>

            {/* Footer */}
            <div className="mt-8">
              {isActive ? (
                <button className="w-full h-12 rounded-xl bg-gradient-to-r from-[#7c3aed] to-[#9333ea] text-white font-medium flex items-center justify-center gap-2 hover:opacity-90 transition">
                  Configure Setup
                  <FaArrowRight size={12} />
                </button>
              ) : (
                <div className="w-full h-12 rounded-xl border border-dashed border-[#e5e7eb] flex items-center justify-center gap-2 text-[#94a3b8] text-sm">
                  <FaLock size={12} />
                  Available Soon
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}