"use client";

import { motion } from "framer-motion";
import {
  Mail,
  Phone,
  MapPin,
  MoreVertical,
} from "lucide-react";

const contacts = [
  {
    initials: "RS",
    name: "Rahul Sharma",
    role: "CEO at Tech Solutions",
    email: "rahul@techsolutions.com",
    phone: "+91 98765 43210",
    city: "Mumbai, India",
    color: "bg-blue-100 text-blue-600",
  },
  {
    initials: "PP",
    name: "Priya Patel",
    role: "Marketing Head at Global Innovators",
    email: "priya@globalinnovators.com",
    phone: "+91 98765 43211",
    city: "Delhi, India",
    color: "bg-green-100 text-green-600",
  },
  {
    initials: "AK",
    name: "Amit Kumar",
    role: "CTO at NextGen Systems",
    email: "amit@nextgensystems.com",
    phone: "+91 98765 43212",
    city: "Bangalore, India",
    color: "bg-purple-100 text-purple-600",
  },
  {
    initials: "SG",
    name: "Sneha Gupta",
    role: "Sales Manager at Apex Corp",
    email: "sneha@apexcorp.com",
    phone: "+91 98765 43213",
    city: "Pune, India",
    color: "bg-orange-100 text-orange-600",
  },
  {
    initials: "VS",
    name: "Vikram Singh",
    role: "Founder at Pioneer Tech",
    email: "vikram@pioneer.com",
    phone: "+91 98765 43214",
    city: "Hyderabad, India",
    color: "bg-pink-100 text-pink-600",
  },
  {
    initials: "NP",
    name: "Neha Pal",
    role: "HR Manager at Bright Future",
    email: "neha@brightfuture.com",
    phone: "+91 98765 43215",
    city: "Ahmedabad, India",
    color: "bg-cyan-100 text-cyan-600",
  },
];

export default function ContactsGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 mt-6">

      {contacts.map((contact, index) => (
        <motion.div
          key={index}
          whileHover={{ y: -3 }}
          className="bg-white border border-[#e5e7eb] rounded-3xl p-6 shadow-sm"
        >

          <div className="flex justify-between">

            <div className="flex gap-4">

              <div
                className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold ${contact.color}`}
              >
                {contact.initials}
              </div>

              <div>
                <h3 className="text-[26px] font-bold text-[#111827]">
                  {contact.name}
                </h3>

                <p className="text-[14px] text-[#64748b]">
                  {contact.role}
                </p>
              </div>

            </div>

            <MoreVertical
              size={20}
              className="text-[#94a3b8]"
            />

          </div>

          <div className="mt-6 space-y-4">

            <div className="flex items-center gap-3 text-[#64748b]">
              <Mail size={18} />
              <span>{contact.email}</span>
            </div>

            <div className="flex items-center gap-3 text-[#64748b]">
              <Phone size={18} />
              <span>{contact.phone}</span>
            </div>

            <div className="flex items-center gap-3 text-[#64748b]">
              <MapPin size={18} />
              <span>{contact.city}</span>
            </div>

          </div>

          <div className="flex gap-3 mt-6">

            <span className="px-4 py-2 rounded-xl bg-green-100 text-green-700 text-sm font-medium">
              Active
            </span>

            <span className="px-4 py-2 rounded-xl bg-purple-100 text-purple-700 text-sm font-medium">
              Premium
            </span>

          </div>

        </motion.div>
      ))}
    </div>
  );
}