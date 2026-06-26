"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import LeadAgingWidget from "./LeadAgingWidget";

interface EmailAnalytics {
  totalEmails: number;
  sentEmails: number;
  failedEmails: number;
  totalClicks: number;
  totalUnsubscribed: number;
  clickThroughRate: string;
}

export default function EmailStats() {
  const [data, setData] = useState<EmailAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  const donutWrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [donutSize, setDonutSize] = useState(180);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const analyticsRes = await fetch("/api/email/analytics");
        const analyticsData = await analyticsRes.json();
        setData(analyticsData);
      } catch (error) {
        console.error("Failed to fetch email data", error);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  const successRate =
    data && data.sentEmails + data.failedEmails > 0
      ? ((data.sentEmails / (data.sentEmails + data.failedEmails)) * 100).toFixed(1)
      : "0";

  const pending = Math.max(
  0,
  (Number(data?.totalEmails) || 0) -
    (Number(data?.sentEmails) || 0) -
    (Number(data?.failedEmails) || 0)
  );

  useEffect(() => {
    const donutEl = donutWrapRef.current;
    if (!donutEl) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        if (entry.target === donutEl) {
          const size = Math.max(120, Math.min(w, 220));
          setDonutSize(size);
        }
      }
    });
    if (donutEl) ro.observe(donutEl);
    return () => ro.disconnect();
  }, []);

  const setupHiDPICanvas = useCallback(
    (canvas: HTMLCanvasElement, width: number, height: number) => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      const ctx = canvas.getContext("2d");
      if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return ctx;
    },
    []
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const size = donutSize;
    const ctx = setupHiDPICanvas(canvas, size, size);
    if (!ctx) return;
    const sent = data?.sentEmails || 0;
    const failed = data?.failedEmails || 0;
    const pend = Math.max(0, pending);
    const total = sent + failed + pend;
    const cx = size / 2;
    const cy = size / 2;
    const radius = size * 0.42;
    const innerRadius = size * 0.29;
    ctx.clearRect(0, 0, size, size);
    if (total === 0) {
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
      ctx.fillStyle = "#e5e7eb";
      ctx.fill();
    } else {
      const segments = [
        { value: sent, color: "#7C3AED" },
        { value: failed, color: "#EF4444" },
        { value: pend, color: "#F59E0B" },
      ];
      let startAngle = -Math.PI / 2;
      segments.forEach((seg) => {
        if (seg.value <= 0) return;
        const sliceAngle = (seg.value / total) * 2 * Math.PI;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
        ctx.closePath();
        ctx.fillStyle = seg.color;
        ctx.fill();
        startAngle += sliceAngle;
      });
    }
    ctx.beginPath();
    ctx.arc(cx, cy, innerRadius, 0, 2 * Math.PI);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    const fontScale = size / 220;
    ctx.textAlign = "center";
    ctx.fillStyle = "#111827";
    ctx.font = `bold ${Math.max(13, 20 * fontScale)}px sans-serif`;
    ctx.fillText(`${successRate}%`, cx, cy + 4 * fontScale);
    ctx.font = `${Math.max(8, 11 * fontScale)}px sans-serif`;
    ctx.fillStyle = "#9ca3af";
    ctx.fillText("Success Rate", cx, cy + 20 * fontScale);
  }, [data, successRate, pending, donutSize, setupHiDPICanvas]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <p className="text-xs text-gray-400">Loading email stats...</p>
      </div>
    );
  }


  console.log("Email Analytics:", data);
  console.log("Pending:", pending);
  
  const stats = [
    {
    label: "Sent",
    value: Number(data?.sentEmails) || 0,
    color: "text-purple-600",
    bg: "bg-purple-50",
    dot: "bg-purple-500",
  },
  {
    label: "Failed",
    value: Number(data?.failedEmails) || 0,
    color: "text-red-500",
    bg: "bg-red-50",
    dot: "bg-red-500",
  },
  {
    label: "Pending",
    value: pending,
    color: "text-amber-500",
    bg: "bg-amber-50",
    dot: "bg-amber-400",
  },
  {
    label: "Click Through",
    value: data?.clickThroughRate
      ? `${data.clickThroughRate}`
      : "0%",
    color: "text-blue-500",
    bg: "bg-blue-50",
    dot: "bg-blue-400",
  },
  {
    label: "Unsubscribed",
    value: Number(data?.totalUnsubscribed) || 0,
    color: "text-orange-500",
    bg: "bg-orange-50",
    dot: "bg-orange-400",
  },
];

 return (
  <div className="bg-gray-50 border border-gray-500 rounded-xl p-4 min-w-0 h-[320px] sm:h-[360px] flex flex-col relative transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
    <div className="flex items-center justify-between mb-4 gap-2 shrink-0">
      <p className="text-sm font-semibold text-gray-700 truncate">Email Status Overview</p>
      <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100 font-medium shrink-0">● Live</span>
    </div>
    <div className="flex flex-col sm:flex-row gap-5 items-center min-w-0 flex-1 min-h-0 overflow-y-auto">
      <div ref={donutWrapRef} className="flex flex-col items-center w-full sm:w-auto sm:shrink-0 max-w-[220px]">
        <canvas ref={canvasRef} style={{ display: "block", maxWidth: "100%" }} />
        <div className="flex gap-3 mt-2 flex-wrap justify-center">
          {[{ label: "Sent", color: "bg-purple-500" }, { label: "Failed", color: "bg-red-500" }, { label: "Pending", color: "bg-amber-400" }].map((l) => (
            <div key={l.label} className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full shrink-0 ${l.color}`} />
              <span className="text-[10px] text-gray-400 whitespace-nowrap">{l.label}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 flex-1 min-w-0 w-full">
        {stats.map((s) => (
          <div key={s.label} className={`${s.bg} rounded-xl px-4 py-3 flex items-center gap-3 min-w-0`}>
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${s.dot}`} />
            <div className="min-w-0">
              <p className="text-xs text-gray-400 truncate">{s.label}</p>
              <p className={`text-base font-bold ${s.color} truncate`}>
                {typeof s.value === "number"
                  ? Number.isFinite(s.value)
                    ? s.value
                    : 0
                  : s.value}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);
}