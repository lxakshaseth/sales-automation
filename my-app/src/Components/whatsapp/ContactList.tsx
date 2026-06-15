"use client";

import { useEffect, useMemo, useState } from "react";

import { Search } from "lucide-react";

import { Contact, getContacts } from "@/services/whatsapp.service";

type ContactListProps = {
  selectedContact: Contact | null;
  onSelectContact: (contact: Contact) => void;
};

export default function ContactList({
  selectedContact,
  onSelectContact,
}: ContactListProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchContacts();

    const interval = setInterval(() => {
      fetchContacts(false);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  async function fetchContacts(showLoader = true) {
    try {
      if (showLoader) {
        setLoading(true);
      }

      const response = await getContacts();

      setContacts(response.data || []);
    } catch (error) {
      console.error(error);
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  }

  const filteredContacts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return contacts.filter((contact) =>
      [contact.customName, contact.name, contact.phone, contact.waId]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(query)),
    );
  }, [contacts, search]);

  return (
    <div className="h-full flex flex-col">
      {/* HEADER */}
      <div className="p-5 border-b border-[#e7ebf3]">
        <h2 className="text-xl font-bold text-[#111827]">Contacts</h2>

        <p className="text-sm text-gray-500 mt-1">Manage customer chats</p>

        <div className="mt-4 relative">
          <Search
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search contacts..."
            className="w-full h-11 pl-10 pr-4 rounded-xl border border-[#e7ebf3] bg-[#fafafa] focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* CONTACT COUNT */}
      <div className="px-5 py-3 border-b border-[#e7ebf3] bg-[#fafafa]">
        <p className="text-sm font-medium text-gray-600">
          {filteredContacts.length} Contacts
        </p>
      </div>

      {/* CONTACT LIST */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-5 space-y-3">
            <div className="h-16 rounded-xl bg-gray-100 animate-pulse" />

            <div className="h-16 rounded-xl bg-gray-100 animate-pulse" />

            <div className="h-16 rounded-xl bg-gray-100 animate-pulse" />
          </div>
        ) : filteredContacts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center px-6">
            <div className="w-16 h-16 rounded-2xl bg-green-100 flex items-center justify-center mb-4">
              <span className="text-2xl">💬</span>
            </div>

            <h3 className="text-lg font-semibold text-[#111827]">
              No Conversations
            </h3>

            <p className="text-gray-500 text-center mt-2 text-sm">
              Customer conversations will appear here once messages start
              arriving.
            </p>
          </div>
        ) : (
          filteredContacts.map((contact) => (
            <div
              key={contact._id}
              onClick={() => onSelectContact(contact)}
              className={`px-5 py-4 border-b border-[#f1f5f9] cursor-pointer transition-all ${
                selectedContact?._id === contact._id
                  ? "bg-green-50 border-l-4 border-l-green-500"
                  : "hover:bg-[#fafafa]"
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-full bg-green-100 flex items-center justify-center font-semibold text-green-700">
                  {(contact.customName || contact.name || contact.phone || "?")
                    .charAt(0)
                    .toUpperCase()}
                </div>

                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-[#111827] truncate">
                    {contact.customName || contact.name || "Unknown Contact"}
                  </p>

                  <p className="text-sm text-gray-500 truncate">
                    {contact.phone}
                  </p>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
