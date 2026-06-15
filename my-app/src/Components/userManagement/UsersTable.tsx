"use client";

import { Search, ChevronDown, MoreVertical, Plus } from "lucide-react";

const users = [
  {
    name: "Snehal Jadhav",
    email: "snehal.jadhav@gmail.com",
    department: "Administration",
    role: "Super Admin",
    status: "Active",
    login: "Today, 10:24 AM",
    image: "https://i.pravatar.cc/100?img=1",
  },
  {
    name: "Rahul Sharma",
    email: "rahul.sharma@gmail.com",
    department: "Sales",
    role: "Manager",
    status: "Active",
    login: "Today, 09:15 AM",
    image: "https://i.pravatar.cc/100?img=2",
  },
  {
    name: "Amit Verma",
    email: "amit.verma@gmail.com",
    department: "Sales",
    role: "Sales",
    status: "Active",
    login: "Yesterday, 06:45 PM",
    image: "https://i.pravatar.cc/100?img=3",
  },
  {
    name: "Priya Singh",
    email: "priya.singh@gmail.com",
    department: "HR",
    role: "HR",
    status: "Inactive",
    login: "2 days ago, 11:30 AM",
    image: "https://i.pravatar.cc/100?img=4",
  },
  {
    name: "Karan Mehta",
    email: "karan.mehta@gmail.com",
    department: "Support",
    role: "Support",
    status: "Active",
    login: "Yesterday, 04:20 PM",
    image: "https://i.pravatar.cc/100?img=5",
  },
];

export default function UserManagementTable() {
  return (
    <div className="bg-white rounded-3xl border border-[#e7ebf3] shadow-sm p-6">

      {/* HEADER + FILTERS */}
<div className="flex items-start justify-between gap-6 mb-8 flex-wrap">

  {/* LEFT */}
  <div>
    <h2 className="text-[26px] font-bold text-[#111827] leading-none">
      User Management
    </h2>

    <p className="text-gray-500 mt-2 text-sm">
      View and manage all users
    </p>
  </div>

  {/* RIGHT */}
  <div className="flex items-center gap-3 flex-wrap">

    <div className="relative">
      <Search
        size={18}
        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400"
      />

      <input
        type="text"
        placeholder="Search users..."
        className="w-[220px] h-11 rounded-xl border border-[#e5e7eb] px-4 text-sm outline-none"
      />
    </div>

    <button className="h-11 px-4 border border-[#e5e7eb] rounded-xl flex items-center gap-2 text-sm text-gray-700">
      Department
      <ChevronDown size={16} />
    </button>

    <button className="h-11 px-4 border border-[#e5e7eb] rounded-xl flex items-center gap-2 text-sm text-gray-700">
      Role
      <ChevronDown size={16} />
    </button>

    <button className="h-11 px-4 border border-[#e5e7eb] rounded-xl flex items-center gap-2 text-sm text-gray-700">
      Status
      <ChevronDown size={16} />
    </button>

    <button className="h-11 px-5 rounded-xl bg-violet-600 text-white flex items-center gap-2 font-medium hover:bg-violet-700 transition">
      <Plus size={18} />
      Add User
    </button>

  </div>

</div>

      {/* TABLE */}
      <div className="overflow-hidden rounded-2xl border border-[#e9edf5]">
        <table className="w-full">
          
          <thead>
            <tr className="bg-[#f8fafc] border-b border-[#e9edf5]">
              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                User
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Email
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Department
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Role
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Status
              </th>

              <th className="px-6 py-4 text-left text-xs font-semibold text-[#64748b] uppercase">
                Last Login
              </th>

              <th className="px-6 py-4 text-center text-xs font-semibold text-[#64748b] uppercase">
                Actions
              </th>
            </tr>
          </thead>

          <tbody>
            {users.map((user, index) => (
              <tr
                key={index}
                className="border-b border-[#edf1f7] hover:bg-[#fafbfc] transition-all"
              >
                <td className="px-6 py-5">
                  <div className="flex items-center gap-3">
                    <img
                      src={user.image}
                      alt=""
                      className="w-10 h-10 rounded-full"
                    />

                    <span className="font-medium text-[#111827]">
                      {user.name}
                    </span>
                  </div>
                </td>

                <td className="px-6 py-5 text-gray-700">
                  {user.email}
                </td>

                <td className="px-6 py-5 text-gray-700">
                  {user.department}
                </td>

                <td className="px-6 py-5">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-violet-100 text-violet-700">
                    {user.role}
                  </span>
                </td>

                <td className="px-6 py-5">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      user.status === "Active"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-600"
                    }`}
                  >
                    {user.status}
                  </span>
                </td>

                <td className="px-6 py-5 text-gray-700">
                  {user.login}
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

      {/* PAGINATION */}
      <div className="flex items-center justify-between mt-6">
        <p className="text-sm text-gray-500">
          Showing 1 to 5 of 156 users
        </p>

        <div className="flex items-center gap-2">

          <button className="w-9 h-9 rounded-xl border border-[#e5e7eb]">
            ←
          </button>

          <button className="w-9 h-9 rounded-xl bg-[#f5f3ff] border border-violet-500 text-violet-700 font-semibold">
            1
          </button>

          <button className="w-9 h-9 rounded-xl">
            2
          </button>

          <button className="w-9 h-9 rounded-xl">
            3
          </button>

          <span>...</span>

          <button className="w-9 h-9 rounded-xl">
            32
          </button>

          <button className="w-9 h-9 rounded-xl border border-[#e5e7eb]">
            →
          </button>

        </div>
      </div>

    </div>
  );
}