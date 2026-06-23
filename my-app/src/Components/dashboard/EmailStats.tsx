"use client";

import { useEffect, useState, useRef } from "react";

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

interface RecentEmail {
  _id: string;
  to: string;
  subject: string;
  status: string;
  createdAt: string;
}

interface DailyStats {
  _id: string;
  sent: number;
  failed: number;
  pending: number;
}

export default function EmailStats() {
  const [data, setData] = useState<EmailAnalytics | null>(null);
  const [recentEmails, setRecentEmails] = useState<RecentEmail[]>([]);
  const [dailyStats, setDailyStats] = useState<DailyStats[]>([]);
  const [loading, setLoading] = useState(true);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const barCanvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [analyticsRes, recentRes, dailyRes] = await Promise.all([
          fetch("/api/email/analytics"),
          fetch("/api/email/recent"),
          fetch("/api/email/daily"),
        ]);
        const analyticsData = await analyticsRes.json();
        const recentData = await recentRes.json();
        const dailyData = await dailyRes.json();

        setData(analyticsData);
        setRecentEmails(recentData.recentEmails || []);
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

  // Donut chart
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const sent = data?.sentEmails || 0;
    const failed = data?.failedEmails || 0;
    const pend = Math.max(0, pending);
    const total = sent + failed + pend;

    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const radius = 100;
    const innerRadius = 68;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

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

    ctx.textAlign = "center";
    ctx.fillStyle = "#111827";
    ctx.font = "bold 20px sans-serif";
    ctx.fillText(`${successRate}%`, cx, cy + 4);
    ctx.font = "11px sans-serif";
    ctx.fillStyle = "#9ca3af";
    ctx.fillText("Success Rate", cx, cy + 20);
  }, [data, successRate, pending]);

  // Bar chart for daily trend
  useEffect(() => {
    const canvas = barCanvasRef.current;
    if (!canvas || dailyStats.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const padding = 30;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    const maxVal = Math.max(...dailyStats.map((d) => d.sent + d.failed + d.pending), 1);
    const barWidth = chartWidth / dailyStats.length / 3 - 2;

    dailyStats.forEach((day, i) => {
      const x = padding + (i * chartWidth) / dailyStats.length;
      const bars = [
        { value: day.sent, color: "#7C3AED" },
        { value: day.failed, color: "#EF4444" },
        { value: day.pending, color: "#F59E0B" },
      ];
      bars.forEach((bar, j) => {
        const barHeight = (bar.value / maxVal) * chartHeight;
        ctx.fillStyle = bar.color;
        ctx.fillRect(
          x + j * (barWidth + 2),
          padding + chartHeight - barHeight,
          barWidth,
          barHeight
        );
      });

      // Date label
      ctx.fillStyle = "#9ca3af";
      ctx.font = "9px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(
        day._id.slice(5),
        x + barWidth * 1.5,
        canvas.height - 5
      );
    });
  }, [dailyStats]);

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

  const statusColor: Record<string, string> = {
    SENT: "text-purple-600 bg-purple-50",
    FAILED: "text-red-500 bg-red-50",
    PENDING: "text-amber-500 bg-amber-50",
  };

  return (
    <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm">📧</span>
          <p className="text-sm font-semibold text-gray-700">
            Email Status Overview
          </p>
        </div>
        <span className="text-[10px] text-purple-600 bg-purple-50 px-2 py-0.5 rounded-full border border-purple-100 font-medium">
          ● Live
        </span>
      </div>

      {/* Donut + Stats */}
      <div className="flex gap-5 items-center">
        <div className="flex flex-col items-center shrink-0">
          <canvas
            ref={canvasRef}
            width={220}
            height={220}
            style={{ display: "block" }}
          />
          <div className="flex gap-3 mt-2">
            {[
              { label: "Sent", color: "bg-purple-500" },
              { label: "Failed", color: "bg-red-500" },
              { label: "Pending", color: "bg-amber-400" },
            ].map((l) => (
              <div key={l.label} className="flex items-center gap-1">
                <span className={`w-2 h-2 rounded-full ${l.color}`} />
                <span className="text-[10px] text-gray-400">{l.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 flex-1">
          {stats.map((s) => (
            <div
              key={s.label}
              className={`${s.bg} rounded-xl px-4 py-3 flex items-center gap-3`}
            >
              <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${s.dot}`} />
              <div>
                <p className="text-xs text-gray-400 leading-tight">{s.label}</p>
                <p className={`text-base font-bold ${s.color} leading-tight`}>{s.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Daily Trend Chart */}
      <div>
        <p className="text-xs font-semibold text-gray-600 mb-2">
          📈 Last 7 Days Trend
        </p>
        {dailyStats.length === 0 ? (
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <p className="text-xs text-gray-400">No data yet</p>
          </div>
        ) : (
          <canvas
            ref={barCanvasRef}
            width={560}
            height={120}
            style={{ display: "block", width: "100%" }}
          />
        )}
        <div className="flex gap-3 mt-1">
          {[
            { label: "Sent", color: "bg-purple-500" },
            { label: "Failed", color: "bg-red-500" },
            { label: "Pending", color: "bg-amber-400" },
          ].map((l) => (
            <div key={l.label} className="flex items-center gap-1">
              <span className={`w-2 h-2 rounded-full ${l.color}`} />
              <span className="text-[10px] text-gray-400">{l.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Emails Table */}
      <div>
        <p className="text-xs font-semibold text-gray-600 mb-2">
          🕐 Recent Emails
        </p>
        {recentEmails.length === 0 ? (
          <div className="bg-gray-50 rounded-xl p-4 text-center">
            <p className="text-xs text-gray-400">No emails sent yet</p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-gray-100">
            <table className="w-full text-xs">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-3 py-2 text-gray-400 font-medium">To</th>
                  <th className="text-left px-3 py-2 text-gray-400 font-medium">Subject</th>
                  <th className="text-left px-3 py-2 text-gray-400 font-medium">Status</th>
                  <th className="text-left px-3 py-2 text-gray-400 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {recentEmails.map((email) => (
                  <tr key={email._id} className="border-t border-gray-50">
                    <td className="px-3 py-2 text-gray-600 truncate max-w-[120px]">
                      {email.to}
                    </td>
                    <td className="px-3 py-2 text-gray-600 truncate max-w-[150px]">
                      {email.subject}
                    </td>
                    <td className="px-3 py-2">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${statusColor[email.status] || "text-gray-500 bg-gray-50"}`}>
                        {email.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-400">
                      {new Date(email.createdAt).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}