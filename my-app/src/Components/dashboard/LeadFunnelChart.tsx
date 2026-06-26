"use client";

import { CalendarDays } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const STATUS_ORDER = ["new", "contacted"];

const STATUS_LABELS: Record<string, string> = {
  new: "New",
  contacted: "Contacted",
};

const STATUS_COLORS: Record<string, string> = {
  new: "#3b82f6",
  contacted: "#1D9E75",
};

interface FunnelItem {
  status: string;
  count: number;
}

interface LeadFunnelChartProps {
  data: FunnelItem[];
  timePeriod: "7" | "30";
  onTimePeriodChange: (period: "7" | "30") => void;
  dateRangeLabel: string;
}

export default function LeadFunnelChart({
  data,
  timePeriod,
  onTimePeriodChange,
  dateRangeLabel,
}: LeadFunnelChartProps) {
  const sortedData = STATUS_ORDER.map((status) => ({
    status,
    label: STATUS_LABELS[status],
    count: data.find((d) => d.status === status)?.count ?? 0,
  }));

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm p-5 transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-[15px] font-semibold text-[#111827]">
          WhatsApp Contacts
        </h3>
        <div className="relative">
          <select
            value={timePeriod}
            onChange={(e) => onTimePeriodChange(e.target.value as "7" | "30")}
            className="appearance-none flex items-center gap-2 pl-8 pr-4 py-2 text-[13px] text-[#64748b] border border-[#e5e7eb] rounded-lg bg-white cursor-pointer"
          >
            <option value="7">Time Period: Last 7 Days</option>
            <option value="30">Time Period: Last 30 Days</option>
          </select>
          <CalendarDays
            size={14}
            className="absolute left-2 top-1/2 -translate-y-1/2 text-[#64748b] pointer-events-none"
          />
        </div>
      </div>
      <p className="text-[12px] text-[#94a3b8] mb-4">{dateRangeLabel}</p>

      <div className="h-[100px]" style={{ minWidth: 0 }}>
        <ResponsiveContainer width="100%" height="100%" minWidth={0}>
          <BarChart
            data={sortedData}
            layout="vertical"
            margin={{ top: 10, right: 40, left: 20, bottom: 10 }}
          >
            <CartesianGrid horizontal={false} stroke="#eef2f7" />

            <XAxis
              type="number"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#64748b", fontSize: 12 }}
            />

            <YAxis
              type="category"
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "#64748b", fontSize: 13 }}
              width={100}
            />

            <Tooltip
              formatter={(value) => [value, "Leads"]}
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e5e7eb",
                background: "#fff",
                boxShadow: "0 10px 25px rgba(0,0,0,0.08)",
                fontSize: "13px",
              }}
            />

            <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={28}>
              {sortedData.map((entry) => (
                <Cell key={entry.status} fill={STATUS_COLORS[entry.status]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
