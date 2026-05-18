"use client";

import { TrendingUp } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

export default function PipelineChart() {
  const pipelineData = [
    { name: 'Jan', leads: 400, sales: 240 },
    { name: 'Feb', leads: 300, sales: 139 },
    { name: 'Mar', leads: 420, sales: 280 },
    { name: 'Apr', leads: 278, sales: 390 },
    { name: 'May', leads: 589, sales: 480 },
    { name: 'Jun', leads: 439, sales: 380 },
    { name: 'Jul', leads: 649, sales: 530 },
  ];

  return (
    <div className="bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm p-6 flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
          <TrendingUp size={18} className="text-violet-500" />
          Lead & Sales Pipeline
        </h3>
      </div>
      <div className="h-75 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={pipelineData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" vertical={false} />
            <XAxis dataKey="name" stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#a1a1aa" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', borderRadius: '8px', color: '#fff' }} itemStyle={{ color: '#fff' }} />
            <Legend iconType="circle" wrapperStyle={{ fontSize: '12px' }} />
            <Line type="monotone" dataKey="leads" name="Leads" stroke="#3b82f6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
            <Line type="monotone" dataKey="sales" name="Sales" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}