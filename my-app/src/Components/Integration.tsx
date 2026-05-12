"use client";

import { FaWhatsapp, FaFacebook, FaInstagram, FaTwitter, FaLinkedin, FaArrowRight, FaLock } from "react-icons/fa";
import { FaMessage } from "react-icons/fa6";
import { MdEmail } from "react-icons/md";

export default function Integration() {
  const integrations = [
    { name: "WhatsApp", icon: FaWhatsapp, status: "Active", color: "text-green-500", bg: "bg-green-100 dark:bg-green-500/20", glow: "bg-green-500", borderGlow: "group-hover:border-green-500/40", desc: "Sync direct messages & set up automated reply campaigns." },
    { name: "Email", icon: MdEmail, status: "Active", color: "text-blue-500", bg: "bg-blue-100 dark:bg-blue-500/20", glow: "bg-blue-500", borderGlow: "group-hover:border-blue-500/40", desc: "Connect Gmail or Outlook to manage email sequences." },
    { name: "Facebook", icon: FaFacebook, status: "Coming Soon", color: "text-blue-600", bg: "bg-blue-100 dark:bg-blue-600/20", glow: "bg-blue-600", borderGlow: "group-hover:border-blue-600/40", desc: "Manage Messenger chats & capture Facebook lead forms." },
    { name: "Instagram", icon: FaInstagram, status: "Coming Soon", color: "text-pink-500", bg: "bg-pink-100 dark:bg-pink-500/20", glow: "bg-pink-500", borderGlow: "group-hover:border-pink-500/40", desc: "Reply to DMs, story mentions, and comments automatically." },
    { name: "Twitter X", icon: FaTwitter, status: "Coming Soon", color: "text-slate-800 dark:text-slate-200", bg: "bg-slate-200 dark:bg-slate-700/50", glow: "bg-slate-500", borderGlow: "group-hover:border-slate-500/40", desc: "Track brand mentions and automate outreach." },
    { name: "LinkedIn", icon: FaLinkedin, status: "Coming Soon", color: "text-blue-700", bg: "bg-blue-100 dark:bg-blue-700/20", glow: "bg-blue-700", borderGlow: "group-hover:border-blue-700/40", desc: "Extract B2B contacts and schedule connection requests." },
    { name: "SMS", icon: FaMessage, status: "Coming Soon", color: "text-violet-500", bg: "bg-violet-100 dark:bg-violet-500/20", glow: "bg-violet-500", borderGlow: "group-hover:border-violet-500/40", desc: "Send highly targeted SMS broadcasts to local leads." },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {integrations.map((integration, index) => {
        const Icon = integration.icon;
        const isActive = integration.status === "Active";
        
        return (
          <div key={index} className="group relative w-full rounded-[2.5rem] transition-all duration-500 hover:-translate-y-2">
            {/* Outer Animated Glow Behind Card */}
            <div className={`absolute -inset-0.5 rounded-[2.5rem] blur-xl opacity-0 group-hover:opacity-40 transition-opacity duration-500 ${isActive ? integration.glow : 'bg-zinc-500'}`} />

            {/* Main Card Content */}
            <div className={`relative flex flex-col h-full bg-white/70 dark:bg-zinc-900/70 backdrop-blur-2xl border transition-colors duration-500 ${isActive ? `border-zinc-200 dark:border-zinc-800 ${integration.borderGlow}` : 'border-dashed border-zinc-200 dark:border-zinc-800'} rounded-[2.5rem] p-8 overflow-hidden z-10 shadow-xl shadow-zinc-200/20 dark:shadow-black/40`}>
              
              {/* Internal Ambient Corner Glow */}
              <div className={`absolute -top-16 -right-16 w-48 h-48 blur-3xl rounded-full transition-opacity duration-700 opacity-20 group-hover:opacity-50 ${integration.glow}`} />

              {/* Top bar: Icon & Status */}
              <div className="flex items-start justify-between mb-8 relative z-20">
                <div className={`w-16 h-16 rounded-[1.25rem] flex items-center justify-center shadow-lg transition-transform duration-500 group-hover:scale-110 group-hover:-rotate-3 ${isActive ? integration.bg : 'bg-zinc-100 dark:bg-zinc-800/50 shadow-none'}`}>
                  <Icon size={30} className={`${isActive ? integration.color : 'text-zinc-400 dark:text-zinc-500'}`} />
                </div>
                <div className="flex items-center">
                  <span className={`flex items-center gap-1.5 text-[10px] uppercase tracking-widest font-bold px-3 py-1.5 rounded-full backdrop-blur-md border ${isActive ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20' : 'bg-zinc-500/10 text-zinc-500 dark:text-zinc-400 border-zinc-500/20'}`}>
                    {isActive && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />}
                    {integration.status}
                  </span>
                </div>
              </div>
              
              {/* Text Section */}
              <div className="relative z-20 mt-2">
                <h3 className={`text-2xl font-bold tracking-tight ${isActive ? 'text-zinc-900 dark:text-white' : 'text-zinc-500 dark:text-zinc-400'}`}>{integration.name}</h3>
                <p className={`mt-3 text-sm leading-relaxed ${isActive ? 'text-zinc-600 dark:text-zinc-400' : 'text-zinc-400 dark:text-zinc-600'}`}>
                  {integration.desc}
                </p>
              </div>
              
              {/* Footer / Action */}
              <div className="mt-auto pt-10 relative z-20">
                {isActive ? (
                  <button className={`w-full flex items-center justify-between px-6 py-4 rounded-2xl text-sm font-semibold transition-all duration-300 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md ${integration.color} group-hover:bg-zinc-50 dark:group-hover:bg-zinc-900`}>
                    <span>Configure Setup</span>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${integration.bg} transition-transform duration-300 group-hover:translate-x-1`}>
                      <FaArrowRight size={12} />
                    </div>
                  </button>
                ) : (
                  <div className="w-full flex items-center justify-center gap-2 px-6 py-4 rounded-2xl text-sm font-medium text-zinc-400 dark:text-zinc-600 bg-zinc-50 dark:bg-zinc-900/30 border border-dashed border-zinc-200 dark:border-zinc-800">
                    <FaLock size={12} />
                    <span>Available in next update</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}