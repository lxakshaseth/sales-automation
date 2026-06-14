"use client";

import { MoreVertical, Plus } from "lucide-react";

const roles = [
  {
    role: "Super Admin",
    users: 12,
    description: "Full system access and control",
  },
  {
    role: "Manager",
    users: 32,
    description: "Manage team and view reports",
  },
  {
    role: "HR",
    users: 8,
    description: "Manage HR operations",
  },
  {
    role: "Sales",
    users: 56,
    description: "Manage leads and sales pipeline",
  },
];

export default function RoleManagement() {
  return (
    <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-6">

      {/* HEADER */}
      <div className="flex items-start justify-between mb-6">

        <div>
          <h2 className="text-[26px] font-bold text-[#111827]">
            Role Management
          </h2>

          <p className="text-gray-500 text-sm mt-1">
            Manage roles and their permissions
          </p>
        </div>

        <button className="h-11 px-5 rounded-xl border border-violet-200 text-violet-600 bg-violet-50 hover:bg-violet-100 transition flex items-center gap-2 font-medium">
          <Plus size={18} />
          Create Role
        </button>

      </div>

      {/* TABLE */}
      <div className="overflow-hidden rounded-2xl border border-[#e9edf5]">

        <table className="w-full">

          <thead>
            <tr className="bg-[#f8fafc] border-b border-[#e9edf5]">

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Role
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Users
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Description
              </th>

              <th className="px-6 py-4 text-center text-xs font-semibold text-[#64748b] uppercase">
                Actions
              </th>

            </tr>
          </thead>

          <tbody>
            {roles.map((item, index) => (
              <tr
                key={index}
                className="border-b border-[#edf1f7] hover:bg-[#fafbfc] transition-all"
              >
                <td className="px-6 py-5">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-violet-100 text-violet-700">
                    {item.role}
                  </span>
                </td>

                <td className="px-6 py-5 text-[#111827] font-medium">
                  {item.users}
                </td>

                <td className="px-6 py-5 text-gray-600">
                  {item.description}
                </td>

                <td className="px-6 py-5 text-center">
                  <button>
                    <MoreVertical
                      size={18}
                      className="text-gray-500"
                    />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>

        </table>

      </div>

      {/* FOOTER */}
      <div className="mt-5">
        <p className="text-sm text-gray-500">
          Showing 1 to 4 of 4 roles
        </p>
      </div>

    </div>
  );
}