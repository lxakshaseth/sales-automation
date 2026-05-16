"use client";

import { useState } from "react";
const columns = [
  {
    title: "New Lead",
    count: 18,
    amount: "₹ 6,25,000",
    color: "#3b82f6",
    leads: [
      {
        name: "Rahul Verma",
        role: "CEO",
        company: "TechNova",
        source: "Website",
        leftAmount: "₹50,000",
        rightAmount: "₹ 50,000",
        initials: "RV",
        avatarColor: "bg-violet-500/20 text-violet-300",
      },
      {
        name: "Priya Singh",
        role: "CTO",
        company: "SoftTech",
        source: "Referral",
        leftAmount: "₹55,000",
        rightAmount: "₹ 75,000",
        initials: "PS",
        avatarColor: "bg-yellow-500/20 text-yellow-300",
      },
      {
        name: "Aman Gupta",
        role: "Manager",
        company: "InnovateX",
        source: "Campaign",
        leftAmount: "₹0rb",
        rightAmount: "₹ 40,000",
        initials: "AG",
        avatarColor: "bg-green-500/20 text-green-300",
      },
    ],
  },

  {
    title: "Contacted",
    count: 22,
    amount: "₹ 9,80,000",
    color: "#facc15",
    leads: [
      {
        name: "Neha Patel",
        role: "Director",
        company: "BrightFuture",
        source: "Last Contact: 2h ago",
        leftAmount: "₹65,000",
        rightAmount: "₹ 65,000",
        initials: "NP",
        avatarColor: "bg-pink-500/20 text-pink-300",
      },
      {
        name: "Vikram Joshi",
        role: "CEO",
        company: "WebSolution",
        source: "Last Contact: 1d ago",
        leftAmount: "₹45,000",
        rightAmount: "₹ 45,000",
        initials: "VJ",
        avatarColor: "bg-green-500/20 text-green-300",
      },
      {
        name: "Karan Mehta",
        role: "Founder",
        company: "DataMind",
        source: "Last Contact: 2d ago",
        leftAmount: "₹20,000",
        rightAmount: "₹ 70,000",
        initials: "KM",
        avatarColor: "bg-blue-500/20 text-blue-300",
      },
    ],
  },

  {
    title: "Qualified",
    count: 20,
    amount: "₹ 12,50,000",
    color: "#22c55e",
    leads: [
      {
        name: "Sneha Iyer",
        role: "CTO",
        company: "CloudNet",
        source: "Score: 85",
        leftAmount: "₹0rb",
        rightAmount: "₹ 1,20,000",
        initials: "SI",
        avatarColor: "bg-orange-500/20 text-orange-300",
      },
      {
        name: "Rohit Malhotra",
        role: "Ops",
        company: "GlobalTech",
        source: "Score: 78",
        leftAmount: "₹8crb",
        rightAmount: "₹ 80,000",
        initials: "RM",
        avatarColor: "bg-violet-500/20 text-violet-300",
      },
      {
        name: "Anjali Desai",
        role: "Manager",
        company: "InnoSoft",
        source: "Score: 75",
        leftAmount: "₹0rb",
        rightAmount: "₹ 90,000",
        initials: "AD",
        avatarColor: "bg-blue-500/20 text-blue-300",
      },
    ],
  },

  {
    title: "Proposal",
    count: 15,
    amount: "₹ 11,25,000",
    color: "#8b5cf6",
    leads: [
      {
        name: "Arjun Nair",
        role: "CEO",
        company: "FutureLabs",
        source: "Proposal Sent: 1d ago",
        leftAmount: "₹2,55,000",
        rightAmount: "₹ 1,50,000",
        initials: "AN",
        avatarColor: "bg-pink-500/20 text-pink-300",
      },
      {
        name: "Meera Kapoor",
        role: "Director",
        company: "SmartWorks",
        source: "Proposal Sent: 2d ago",
        leftAmount: "₹95,000",
        rightAmount: "₹ 95,000",
        initials: "MK",
        avatarColor: "bg-yellow-500/20 text-yellow-300",
      },
      {
        name: "Siddharth Rao",
        role: "CTO",
        company: "NextGen",
        source: "Proposal Sent: 3d ago",
        leftAmount: "₹2,50,000",
        rightAmount: "₹ 1,30,000",
        initials: "SR",
        avatarColor: "bg-green-500/20 text-green-300",
      },
    ],
  },

  {
    title: "Negotiation",
    count: 10,
    amount: "₹ 6,75,000",
    color: "#f97316",
    leads: [
      {
        name: "Pooja Sharma",
        role: "Head",
        company: "BizCorp",
        source: "Last Update: 2h ago",
        leftAmount: "₹2,90,000",
        rightAmount: "₹ 85,000",
        initials: "PS",
        avatarColor: "bg-violet-500/20 text-violet-300",
      },
      {
        name: "Harsh Agarwal",
        role: "CEO",
        company: "HexaSoft",
        source: "Last Update: 1d ago",
        leftAmount: "₹35,000",
        rightAmount: "₹ 1,20,000",
        initials: "HA",
        avatarColor: "bg-green-500/20 text-green-300",
      },
      {
        name: "Divya Jain",
        role: "COO",
        company: "Skyline Tech",
        source: "Last Update: 2d ago",
        leftAmount: "₹25,000",
        rightAmount: "₹ 70,000",
        initials: "DJ",
        avatarColor: "bg-pink-500/20 text-pink-300",
      },
    ],
  },

  {
    title: "Won",
    count: 21,
    amount: "₹ 2,95,000",
    color: "#22c55e",
    leads: [
      {
        name: "Amit Kumar",
        role: "CEO",
        company: "RapidOps",
        source: "Won on: 10 May 2024",
        leftAmount: "₹50,000",
        rightAmount: "₹ 50,000",
        initials: "AK",
        avatarColor: "bg-green-500/20 text-green-300",
      },
      {
        name: "Sunil Reddy",
        role: "CTO",
        company: "SoftEdge",
        source: "Won on: 09 May 2024",
        leftAmount: "₹7,20,000",
        rightAmount: "₹ 75,000",
        initials: "SR",
        avatarColor: "bg-pink-500/20 text-pink-300",
      },
      {
        name: "Nisha Agarwal",
        role: "Manager",
        company: "TechHub",
        source: "Won on: 08 May 2024",
        leftAmount: "₹0rb",
        rightAmount: "₹ 60,000",
        initials: "NA",
        avatarColor: "bg-orange-500/20 text-orange-300",
      },
    ],
  },

  {
    title: "Lost",
    count: 10,
    amount: "₹ 1,25,000",
    color: "#ef4444",
    leads: [
      {
        name: "Deepak Singh",
        role: "CEO",
        company: "OddBridge",
        source: "Lost Reason: Budget",
        leftAmount: "₹50,000",
        rightAmount: "₹ 50,000",
        initials: "DS",
        avatarColor: "bg-red-500/20 text-red-300",
      },
      {
        name: "Kavya Rathi",
        role: "CTO",
        company: "AlphaX",
        source: "Lost Reason: No Need",
        leftAmount: "₹35,000",
        rightAmount: "₹ 35,000",
        initials: "KR",
        avatarColor: "bg-yellow-500/20 text-yellow-300",
      },
      {
        name: "Nitin Bansal",
        role: "Manager",
        company: "BetaSoft",
        source: "Lost Reason: Competitor",
        leftAmount: "₹50,000",
        rightAmount: "₹ 50,000",
        initials: "NB",
        avatarColor: "bg-green-500/20 text-green-300",
      },
    ],
  },
];


export default function PipelineBoard() {
  const [openMenu, setOpenMenu] = useState<number | null>(null);

  // COLUMN STATE
  const [pipelineData, setPipelineData] = useState(columns);

  // DELETE PIPELINE
  const handleDeletePipeline = (indexToDelete: number) => {
    const updated = pipelineData.filter(
      (_, index) => index !== indexToDelete
    );

    setPipelineData(updated);
    setOpenMenu(null);
  };

  // EDIT PIPELINE
  const handleEditPipeline = (index: number) => {
    const newTitle = prompt("Enter new pipeline name");

    if (!newTitle) return;

    const updated = [...pipelineData];

    updated[index].title = newTitle;

    setPipelineData(updated);
    setOpenMenu(null);
  };

  // MOVE PIPELINE LEFT
  const handleMoveLeft = (index: number) => {
    if (index === 0) return;

    const updated = [...pipelineData];

    [updated[index - 1], updated[index]] = [
      updated[index],
      updated[index - 1],
    ];

    setPipelineData(updated);
    setOpenMenu(null);
  };

  // MOVE PIPELINE RIGHT
  const handleMoveRight = (index: number) => {
    if (index === pipelineData.length - 1) return;

    const updated = [...pipelineData];

    [updated[index + 1], updated[index]] = [
      updated[index],
      updated[index + 1],
    ];

    setPipelineData(updated);
    setOpenMenu(null);
  };

  return (
    <div className="flex gap-5 mt-6 overflow-x-auto pb-4 pipeline-scroll">
      {pipelineData.map((column, index) => (
        <div
          key={index}
          className="min-w-[300px] max-w-[300px] h-auto bg-[#111117] border border-[#23232d] rounded-3xl overflow-hidden flex-shrink-0 flex flex-col"
        >
          {/* TOP COLOR LINE */}
          <div
            className="h-1 w-full"
            style={{ background: column.color }}
          />

          <div className="p-4">
            {/* HEADER */}
            <div className="flex items-start justify-between mb-4 relative">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-white font-bold text-lg">
                    {column.title}
                  </h2>

                  <span className="text-xs text-gray-400">
                    {column.count}
                  </span>
                </div>

                <p className="text-gray-400 text-sm mt-2">
                  {column.amount}
                </p>
              </div>

              {/* 3 DOT BUTTON */}
              <button
                onClick={() =>
                  setOpenMenu(openMenu === index ? null : index)
                }
                className="text-gray-500 hover:text-white transition-all text-xl"
              >
                ⋮
              </button>

              {/* DROPDOWN */}
              {openMenu === index && (
                <div
                  className="
                    absolute top-10 right-0
                    w-56
                    bg-[#141419]
                    border border-[#24242b]
                    rounded-2xl
                    p-2
                    shadow-2xl
                    z-50
                  "
                >
                  <div className="space-y-1">

                    {/* EDIT */}
                    <button
                      onClick={() => handleEditPipeline(index)}
                      className="w-full text-left px-4 py-3 rounded-xl text-white hover:bg-[#1f1f27] transition-all"
                    >
                      Edit Pipeline
                    </button>

                    {/* VIEW */}
                    <button
                      className="w-full text-left px-4 py-3 rounded-xl text-white hover:bg-[#1f1f27] transition-all"
                    >
                      View Leads
                    </button>

                    {/* ADD */}
                    <button
                      className="w-full text-left px-4 py-3 rounded-xl text-white hover:bg-[#1f1f27] transition-all"
                    >
                      Add New Lead
                    </button>

                    {/* MOVE LEFT */}
                    <button
                      onClick={() => handleMoveLeft(index)}
                      className="w-full text-left px-4 py-3 rounded-xl text-white hover:bg-[#1f1f27] transition-all"
                    >
                      Move Left
                    </button>

                    {/* MOVE RIGHT */}
                    <button
                      onClick={() => handleMoveRight(index)}
                      className="w-full text-left px-4 py-3 rounded-xl text-white hover:bg-[#1f1f27] transition-all"
                    >
                      Move Right
                    </button>

                    {/* EXPORT */}
                    <button
                      className="w-full text-left px-4 py-3 rounded-xl text-white hover:bg-[#1f1f27] transition-all"
                    >
                      Export Data
                    </button>

                    {/* DELETE */}
                    <button
                      onClick={() => handleDeletePipeline(index)}
                      className="w-full text-left px-4 py-3 rounded-xl text-red-500 hover:bg-[#1f1f27] transition-all"
                    >
                      Delete Pipeline
                    </button>

                  </div>
                </div>
              )}
            </div>

            {/* LEADS */}
            <div className="space-y-4 flex-1">
              {column.leads.map((lead, i) => (
                <div
                  key={i}
                  className="
                    bg-[#181820]
                    border border-[#2a2a35]
                    rounded-2xl
                    p-4
                    h-[150px]
                    flex flex-col justify-between
                    transition-all duration-300
                    hover:-translate-y-2
                    hover:shadow-[0_0_25px_rgba(59,130,246,0.25)]
                    hover:border-blue-500
                    cursor-pointer
                  "
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-white font-semibold text-sm">
                        {lead.name}
                      </h3>

                      <p className="text-gray-400 text-xs mt-1">
                        {lead.role}
                      </p>

                      <p className="text-gray-500 text-xs mt-1">
                        {lead.company}
                      </p>

                      <p className="text-gray-500 text-xs mt-1">
                        {lead.source}
                      </p>
                    </div>

                    <div
                      className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold ${lead.avatarColor}`}
                    >
                      {lead.initials}
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-4">
                    <span className="text-gray-400 text-sm">
                      {lead.leftAmount}
                    </span>

                    <span className="text-white text-sm font-semibold">
                      {lead.rightAmount}
                    </span>
                  </div>
                </div>
              ))}

              <button className="w-full text-violet-400 text-sm font-medium py-2 hover:text-violet-300 transition-all">
                + Add Lead
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}