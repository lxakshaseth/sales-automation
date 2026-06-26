"use client";

import { useCallback, useEffect, useMemo, useState } from "react"; // React hooks for managing state and side effects

import {
  Check,
  CheckCheck,
  Search,
  XCircle,
} from "lucide-react";

import {
  Contact,
  Message,
  getContacts,
} from "@/services/whatsapp.service";

type ContactListProps = {
  selectedContact: Contact | null;
  onSelectContact: (contact: Contact) => void;
  readContactMarker?: {
    waId: string;
    version: number;
  } | null;
};

export default function ContactList({
  selectedContact,
  onSelectContact,
  readContactMarker,
}: ContactListProps) {
  const [contacts, setContacts] = useState<Contact[]>([]);

  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");

  const fetchContacts = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) {
        setLoading(true);
      }

      const response = await getContacts();

      setContacts(response.data || []);
    } catch (error) {
      console.warn("[whatsapp:contacts] fetch failed", {
        error,
      });
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void Promise.resolve().then(() => fetchContacts());

    const interval = setInterval(() => {
      void fetchContacts(false);
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchContacts]);

  useEffect(() => {
    if (!readContactMarker) {
      return;
    }

    void Promise.resolve().then(() => {
      setContacts((currentContacts) =>
        currentContacts.map((contact) =>
          contact.waId === readContactMarker.waId
            ? {
                ...contact,
                unreadCount: 0,
              }
            : contact,
        ),
      );
    });
  }, [readContactMarker]);

  const filteredContacts = useMemo(() => {
    const query = search.trim().toLowerCase();

    return contacts.filter((contact) =>
      [contact.customName, contact.name, contact.phone, contact.waId]
        .filter(Boolean)
        .some((value) => value!.toLowerCase().includes(query)),
    );
  }, [contacts, search]);

  function formatContactTime(timestamp?: string) {
    if (!timestamp) {
      return "";
    }

    const value = new Date(timestamp);
    const today = new Date();
    const isToday =
      value.getFullYear() === today.getFullYear() &&
      value.getMonth() === today.getMonth() &&
      value.getDate() === today.getDate();

    if (isToday) {
      return value.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    return value.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "2-digit",
    });
  }

  function getContactPreview(contact: Contact) {
    if (!contact.lastMessage) {
      return contact.phone || contact.waId;
    }

    return contact.lastMessageDirection === "OUTBOUND"
      ? `You: ${contact.lastMessage}`
      : contact.lastMessage;
  }

  function renderStatusIcon(status?: Message["status"]) {
    switch (status) {
      case "SENT":
        return <Check size={13} className="shrink-0 text-gray-400" />;

      case "DELIVERED":
        return <CheckCheck size={13} className="shrink-0 text-gray-400" />;

      case "READ":
        return <CheckCheck size={13} className="shrink-0 text-blue-500" />;

      case "FAILED":
        return <XCircle size={13} className="shrink-0 text-red-500" />;

      default:
        return null;
    }
  }

  function handleSelectContact(contact: Contact) {
    const readContact = {
      ...contact,
      unreadCount: 0,
    };

    setContacts((currentContacts) =>
      currentContacts.map((currentContact) =>
        currentContact._id === contact._id ? readContact : currentContact,
      ),
    );
    onSelectContact(readContact);
  }

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
          filteredContacts.map((contact) => {
            const isSelected = selectedContact?._id === contact._id;
            const unreadCount = isSelected ? 0 : contact.unreadCount || 0;
            const hasUnread = unreadCount > 0;

            return (
              <div
                key={contact._id}
                onClick={() => handleSelectContact(contact)}
                className={`px-5 py-4 border-b border-[#f1f5f9] cursor-pointer transition-all ${
                  isSelected
                    ? "bg-green-50 border-l-4 border-l-green-500"
                    : "hover:bg-[#fafafa]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 shrink-0 rounded-full bg-green-100 flex items-center justify-center font-semibold text-green-700">
                    {(
                      contact.customName ||
                      contact.name ||
                      contact.phone ||
                      "?"
                    )
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <p
                        className={`truncate ${
                          hasUnread
                            ? "font-bold text-[#111827]"
                            : "font-semibold text-[#111827]"
                        }`}
                      >
                        {contact.customName ||
                          contact.name ||
                          "Unknown Contact"}
                      </p>

                      <span
                        className={`shrink-0 text-[11px] ${
                          hasUnread
                            ? "font-semibold text-green-600"
                            : "text-gray-400"
                        }`}
                      >
                        {formatContactTime(
                          contact.lastMessageCreatedAt || contact.lastMessageAt,
                        )}
                      </span>
                    </div>

                    <div className="mt-1 flex items-center justify-between gap-3">
                      <div
                        className={`min-w-0 flex flex-1 items-center gap-1.5 text-sm ${
                          hasUnread
                            ? "font-semibold text-[#111827]"
                            : "text-gray-500"
                        }`}
                      >
                        {contact.lastMessageDirection === "OUTBOUND" &&
                          renderStatusIcon(contact.lastMessageStatus)}

                        <p className="truncate">
                          {getContactPreview(contact)}
                        </p>
                      </div>

                      {hasUnread && (
                        <span
                          className="flex h-5 w-5 shrink-0 items-center justify-center"
                          aria-label={`${unreadCount} unread customer ${
                            unreadCount === 1 ? "message" : "messages"
                          }`}
                          title={`${unreadCount} unread customer ${
                            unreadCount === 1 ? "message" : "messages"
                          }`}
                        >
                          <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
