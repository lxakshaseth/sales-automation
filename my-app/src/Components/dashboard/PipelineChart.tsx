"use client";

import { TrendingUp, CalendarDays } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Area,
} from "recharts";

const pipelineData = [
  { month: "Jan", leads: 400, sales: 220 },
  { month: "Feb", leads: 300, sales: 120 },
  { month: "Mar", leads: 430, sales: 240 },
  { month: "Apr", leads: 560, sales: 380 },
  { month: "May", leads: 410, sales: 320 },
  { month: "Jun", leads: 540, sales: 410 },
  { month: "Jul", leads: 720, sales: 580 },
];

export default function PipelineChart() {
  return (
    <div className="bg-white border border-[#e8edf5] rounded-[20px] shadow-sm p-5">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        
        <h3 className="flex items-center gap-2 text-[15px] font-semibold text-[#111827]">
          <TrendingUp
            size={16}
            className="text-[#8b5cf6]"
          />
          Lead & Sales Pipeline
        </h3>

        <button className="flex items-center gap-2 px-3 py-2 text-[13px] text-[#64748b] border border-[#e5e7eb] rounded-lg bg-white">
          <CalendarDays size={14} />
          Last 7 Months
        </button>

      </div>

      {/* Chart */}
      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={pipelineData}
            margin={{
              top: 10,
              right: 10,
              left: -15,
              bottom: 20,
            }}
          >
            <CartesianGrid
              vertical={false}
              stroke="#eef2f7"
            />

            <XAxis
              dataKey="month"
              axisLine={false}
              tickLine={false}
              tick={{
                fill: "#64748b",
                fontSize: 12,
              }}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{
                fill: "#64748b",
                fontSize: 12,
              }}
            />

            <Tooltip
              contentStyle={{
                borderRadius: "12px",
                border: "1px solid #e5e7eb",
                background: "#fff",
                boxShadow:
                  "0 10px 25px rgba(0,0,0,0.08)",
              }}
            />

            {/* Light Background Fill */}
            <Area
              type="monotone"
              dataKey="leads"
              fill="#3b82f6"
              fillOpacity={0.05}
              stroke="none"
            />

            <Area
              type="monotone"
              dataKey="sales"
              fill="#8b5cf6"
              fillOpacity={0.05}
              stroke="none"
            />

            {/* Leads */}
            <Line
              type="monotone"
              dataKey="leads"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={{
                r: 4,
                fill: "#3b82f6",
                strokeWidth: 0,
              }}
              activeDot={{
                r: 6,
              }}
            />

            {/* Sales */}
            <Line
              type="monotone"
              dataKey="sales"
              stroke="#8b5cf6"
              strokeWidth={3}
              dot={{
                r: 4,
                fill: "#8b5cf6",
                strokeWidth: 0,
              }}
              activeDot={{
                r: 6,
              }}
            />

            <Legend
              verticalAlign="bottom"
              align="center"
              iconType="circle"
              wrapperStyle={{
                paddingTop: "15px",
                fontSize: "13px",
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}