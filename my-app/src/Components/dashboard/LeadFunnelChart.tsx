"use client";

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
  new: "New Chats",
  contacted: "Active Chats",
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
}

export default function LeadFunnelChart({ data }: LeadFunnelChartProps) {
  const sortedData = STATUS_ORDER.map((status) => ({
    status,
    label: STATUS_LABELS[status],
    count: data.find((d) => d.status === status)?.count ?? 0,
  }));

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm px-5 py-4 transition-all duration-200 ease-out hover:-translate-y-1 hover:shadow-2xl hover:shadow-gray-400/50 hover:z-20 cursor-default">
      {/* Header */}
      <div className="pb-3 border-b border-gray-200">
        <h3 className="text-[15px] font-semibold text-[#111827]">
          WhatsApp Contacts
        </h3>
      </div>

      {/* Chart */}
      <div className="mt-4 h-[90px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={sortedData}
            layout="vertical"
            margin={{
              top: 0,
              right: 20,
              left: 5,
              bottom: 0,
            }}
          >
            <CartesianGrid horizontal={false} stroke="#eef2f7" />

            <XAxis
              type="number"
              axisLine={false}
              tickLine={false}
              tick={{
                fill: "#64748b",
                fontSize: 11,
              }}
            />

            <YAxis
              type="category"
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{
                fill: "#64748b",
                fontSize: 13,
              }}
              width={95}
            />

            <Tooltip
              formatter={(value) => [value, "Contacts"]}
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e5e7eb",
                background: "#fff",
                boxShadow: "0 10px 25px rgba(0,0,0,0.08)",
                fontSize: "13px",
              }}
            />

            <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={22}>
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
