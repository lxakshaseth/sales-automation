"use client";

import { useEffect, useState, useRef, useCallback } from "react";

interface EmailAnalytics {
  totalEmails: number;
  sentEmails: number;
  failedEmails: number;
  totalClicks: number;
  totalOpens: number;
  totalUnsubscribed: number;
  clickThroughRate: string;
  openRate: string;
}

interface DailyStats {
  _id: string;
  sent: number;
  failed: number;
  pending: number;
}

type Metric = "sent" | "failed" | "pending";

const METRIC_LABELS: Record<Metric, string> = {
  sent: "Emails Sent",
  failed: "Emails Failed",
  pending: "Emails Pending",
};

const METRIC_COLORS: Record<Metric, string> = {
  sent: "#7C3AED",
  failed: "#EF4444",
  pending: "#F59E0B",
};

export default function EmailStats() {
  const [data, setData] = useState<EmailAnalytics | null>(null);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState<Metric>("sent");
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const donutWrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const barWrapRef = useRef<HTMLDivElement>(null);
  const barCanvasRef = useRef<HTMLCanvasElement>(null);

  const [donutSize, setDonutSize] = useState(180);
  const [barSize, setBarSize] = useState({ width: 450, height: 260 });

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [analyticsRes, dailyRes] = await Promise.all([
          fetch("/api/email/analytics"),
          fetch("/api/email/daily"),
        ]);
        const analyticsData = await analyticsRes.json();
        const dailyData = await dailyRes.json();

        setData(analyticsData);
        setDailyStats(dailyData.last7Days || []);
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

  const pending = data
    ? data.totalEmails - data.sentEmails - data.failedEmails
    : 0;

  // --- Build a full 7-day series, zero-filling any missing dates ---
  const last7DaysFilled: DailyStats[] = (() => {
    const map = new Map(dailyStats.map((d) => [d._id, d]));
    const days: DailyStats[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10); // YYYY-MM-DD
      days.push(map.get(key) || { _id: key, sent: 0, failed: 0, pending: 0 });
    }
    return days;
  })();

  // --- Responsive sizing ---
  useEffect(() => {
    const donutEl = donutWrapRef.current;
    const barEl = barWrapRef.current;
    if (!donutEl && !barEl) return;

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = entry.contentRect.width;
        if (entry.target === donutEl) {
          const size = Math.max(120, Math.min(w, 220));
          setDonutSize(size);
        }
        if (entry.target === barEl) {
          const width = Math.max(220, w);
          const height = Math.min(300, Math.max(180, width * 0.55));
          setBarSize({ width, height });
        }
      }
    });

    if (donutEl) ro.observe(donutEl);
    if (barEl) ro.observe(barEl);

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

  // "Nice" rounded max for axis (5, 10, 15, 20, 25, 50, 100...)
  const niceMax = (value: number) => {
    if (value <= 5) return 5;
    const step = value <= 20 ? 5 : value <= 50 ? 10 : value <= 100 ? 20 : 50;
    return Math.ceil((value + 1) / step) * step;
  };

  // Donut chart (unchanged)
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

  // Bar chart for selected metric — single series, all 7 days, dotted grid, value labels
  useEffect(() => {
    const canvas = barCanvasRef.current;
    if (!canvas) return;

    const { width, height } = barSize;
    const ctx = setupHiDPICanvas(canvas, width, height);
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const padding = { top: 28, right: 12, bottom: 28, left: 30 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const values = last7DaysFilled.map((d) => d[metric]);
    const rawMax = Math.max(...values, 1);
    const maxValue = niceMax(rawMax);
    const color = METRIC_COLORS[metric];

    // Dotted Y-axis grid
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 3]);

    const steps = 3; // e.g. 0, mid, max -> matches sparse look of target
    for (let i = 0; i <= steps; i++) {
      const y = padding.top + (chartHeight / steps) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      const value = Math.round(maxValue - (maxValue / steps) * i);
      ctx.fillStyle = "#9ca3af";
      ctx.font = "9px sans-serif";
      ctx.textAlign = "right";
      ctx.setLineDash([]);
      ctx.fillText(value.toString(), padding.left - 6, y + 3);
      ctx.setLineDash([2, 3]);
    }
    ctx.setLineDash([]);

    const groupWidth = chartWidth / last7DaysFilled.length;
    const barWidth = Math.max(10, Math.min(32, groupWidth * 0.45));

    last7DaysFilled.forEach((day, index) => {
      const groupX = padding.left + index * groupWidth;
      const value = day[metric];
      const barHeight = (value / maxValue) * chartHeight;
      const x = groupX + (groupWidth - barWidth) / 2;
      const y = padding.top + chartHeight - barHeight;

      // Bar
      ctx.fillStyle = value > 0 ? color : "#e5e7eb";
      ctx.beginPath();
      const r = Math.min(4, barWidth / 2);
      ctx.moveTo(x, y + barHeight);
      ctx.lineTo(x, y + r);
      ctx.arcTo(x, y, x + r, y, r);
      ctx.lineTo(x + barWidth - r, y);
      ctx.arcTo(x + barWidth, y, x + barWidth, y + r, r);
      ctx.lineTo(x + barWidth, y + barHeight);
      ctx.closePath();
      ctx.fill();

      // Value label on top of bar (only if > 0)
      if (value > 0) {
        ctx.fillStyle = "#111827";
        ctx.font = "bold 10px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(value.toString(), groupX + groupWidth / 2, y - 6);
      }

      // X-axis label (MM-DD)
      ctx.fillStyle = "#6b7280";
      ctx.font = "9px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(
        day._id.slice(5),
        groupX + groupWidth / 2,
        height - 10
      );
    });
  }, [last7DaysFilled, metric, barSize, setupHiDPICanvas]);

  if (loading) {
    return (
      <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <p className="text-xs text-gray-400">Loading email stats...</p>
      </div>
    );
  }

  const stats = [
    { label: "Sent", value: data?.sentEmails || 0, color: "text-purple-600", bg: "bg-purple-50", dot: "bg-purple-500" },
    { label: "Failed", value: data?.failedEmails || 0, color: "text-red-500", bg: "bg-red-50", dot: "bg-red-500" },
    { label: "Pending", value: pending, color: "text-amber-500", bg: "bg-amber-50", dot: "bg-amber-400" },
    { label: "Click Through", value: data?.clickThroughRate || "0%", color: "text-blue-500", bg: "bg-blue-50", dot: "bg-blue-400" },
    { label: "Unsubscribed", value: data?.totalUnsubscribed || 0, color: "text-orange-500", bg: "bg-orange-50", dot: "bg-orange-400" },
  ];

return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 w-full min-w-0">

      {/* Left Section */}
      <div className="bg-gray-50 border border-gray-500 rounded-xl p-4 min-w-0 h-[320px] sm:h-[360px] flex flex-col relative transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
        <div className="flex items-center justify-between mb-4 gap-2 shrink-0">
          <p className="text-sm font-semibold text-gray-700 truncate">
            Email Status Overview
          </p>
          <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100 font-medium shrink-0">
            ● Live
          </span>
        </div>

        <div className="flex flex-col sm:flex-row gap-5 items-center min-w-0 flex-1 min-h-0 overflow-y-auto">
          <div
            ref={donutWrapRef}
            className="flex flex-col items-center w-full sm:w-auto sm:shrink-0 max-w-[220px]"
          >
            <canvas ref={canvasRef} style={{ display: "block", maxWidth: "100%" }} />
            <div className="flex gap-3 mt-2 flex-wrap justify-center">
              {[
                { label: "Sent", color: "bg-purple-500" },
                { label: "Failed", color: "bg-red-500" },
                { label: "Pending", color: "bg-amber-400" },
              ].map((l) => (
                <div key={l.label} className="flex items-center gap-1">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${l.color}`} />
                  <span className="text-[10px] text-gray-400 whitespace-nowrap">{l.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 flex-1 min-w-0 w-full">
            {stats.map((s) => (
              <div
                key={s.label}
                className={`${s.bg} rounded-xl px-4 py-3 flex items-center gap-3 min-w-0`}
              >
                <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${s.dot}`} />
                <div className="min-w-0">
                  <p className="text-xs text-gray-400 truncate">{s.label}</p>
                  <p className={`text-base font-bold ${s.color} truncate`}>
                    {s.value}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Section */}
      <div className="bg-gray-50 border border-gray-500 rounded-xl p-4 min-w-0 h-[320px] sm:h-[360px] flex flex-col relative transition-all duration-200 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
        <div className="flex items-center justify-between mb-3 relative shrink-0">
          <p className="text-xs font-semibold text-gray-600">
            Last 7 Days Trend
          </p>

          {/* Metric dropdown */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen((v) => !v)}
              className="text-[11px] font-medium text-gray-600 bg-white border border-gray-200 rounded-lg px-2.5 py-1 flex items-center gap-1 shadow-sm"
            >
              {METRIC_LABELS[metric]}
              <span className="text-gray-400">▾</span>
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-1 w-36 bg-white border border-gray-100 rounded-lg shadow-md z-10 overflow-hidden">
                {(Object.keys(METRIC_LABELS) as Metric[]).map((m) => (
                  <button
                    key={m}
                    onClick={() => {
                      setMetric(m);
                      setDropdownOpen(false);
                    }}
                    className={`w-full text-left text-[11px] px-3 py-2 hover:bg-gray-50 ${
                      m === metric ? "text-violet-600 font-medium" : "text-gray-600"
                    }`}
                  >
                    {METRIC_LABELS[m]}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div ref={barWrapRef} className="w-full min-w-0 flex-1 min-h-0 flex items-center">
          <canvas
            ref={barCanvasRef}
            style={{ display: "block", width: "100%", maxWidth: "100%" }}
          />
        </div>
      </div>
    </div>
);
}