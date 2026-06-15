"use client";

import { useEffect, useState, useRef } from "react";

import { ArrowLeft, Check, CheckCheck, Pencil } from "lucide-react";

import MessageInput from "./MessageInput";

import {
  Contact,
  Message,
  getChatByWaId,
  updateContactName,
  markChatAsRead,
} from "@/services/whatsapp.service";

type ChatWindowProps = {
  selectedContact: Contact | null;
  onBack: () => void;
  onContactUpdated: (contact: Contact) => void;
};

export default function ChatWindow({
  selectedContact,
  onBack,
  onContactUpdated,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);

  const [loading, setLoading] = useState(false);

  const [showRenameModal, setShowRenameModal] = useState(false);

  const [customName, setCustomName] = useState("");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);

  const shouldAutoScrollRef = useRef(true);

  const previousMessageCountRef = useRef(0);

  useEffect(() => {
    if (!selectedContact) return;

    fetchChat();
  }, [selectedContact]);

  useEffect(() => {
    if (!selectedContact) return;

    const interval = setInterval(() => {
      fetchChat(false);
    }, 3000);

    return () => clearInterval(interval);
  }, [selectedContact]);

  useEffect(() => {
    if (!selectedContact) return;

    async function handleReadReceipt() {
      if (!isAtBottom()) return;

      try {
        await markChatAsRead(selectedContact.waId);
      } catch (error) {
        console.error(error);
      }
    }

    handleReadReceipt();
  }, [messages, selectedContact]);

  useEffect(() => {
    const container = messagesContainerRef.current;

    if (!container || !selectedContact) {
      return;
    }

    const handleScrollRead = async () => {
      if (!isAtBottom()) return;

      try {
        await markChatAsRead(selectedContact.waId);
      } catch (error) {
        console.error(error);
      }
    };

    container.addEventListener("scroll", handleScrollRead);

    return () => {
      container.removeEventListener("scroll", handleScrollRead);
    };
  }, [selectedContact]);

  useEffect(() => {
    const hasNewMessage = messages.length > previousMessageCountRef.current;

    if (hasNewMessage && shouldAutoScrollRef.current) {
      messagesEndRef.current?.scrollIntoView({
        behavior: "smooth",
      });
    }

    previousMessageCountRef.current = messages.length;
  }, [messages]);

  async function fetchChat(showLoader = true) {
    if (!selectedContact) return;

    try {
      if (showLoader) {
        setLoading(true);
      }

      const response = await getChatByWaId(selectedContact.waId);

      setMessages(response.data?.messages || []);

      if (showLoader) {
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({
            behavior: "auto",
          });
        }, 100);
      }
    } catch (error) {
      console.error(error);
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  }

  async function handleRenameContact() {
    if (!selectedContact) return;

    if (!customName.trim()) {
      return;
    }

    try {
      const response = await updateContactName(
        selectedContact._id,
        customName.trim(),
      );

      onContactUpdated(response.data);

      setShowRenameModal(false);
      setCustomName("");
    } catch (error) {
      console.error(error);
    }
  }

  function renderStatusIcon(status?: string) {
    switch (status) {
      case "SENT":
        return <Check size={14} className="inline" />;

      case "DELIVERED":
        return <CheckCheck size={14} className="inline" />;

      case "READ":
        return <CheckCheck size={14} className="inline text-blue-300" />;

      case "FAILED":
        return <span className="text-red-300">❌</span>;

      default:
        return null;
    }
  }

  function handleScroll() {
    const container = messagesContainerRef.current;

    if (!container) return;

    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    shouldAutoScrollRef.current = distanceFromBottom < 150;
  }

  function isAtBottom() {
    const container = messagesContainerRef.current;

    if (!container) return false;

    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;

    return distanceFromBottom < 100;
  }

  if (!selectedContact) {
    return (
      <div className="h-full flex flex-col">
        <div className="h-[80px] border-b border-[#e7ebf3] px-6 flex items-center">
          <div>
            <h2 className="text-lg font-semibold text-[#111827]">
              Select a Conversation
            </h2>

            <p className="text-sm text-gray-500">
              Choose a contact to start chatting
            </p>
          </div>
        </div>

        <div className="flex-1 bg-[#f8fafc] flex items-center justify-center">
          <div className="text-center max-w-sm">
            <div className="text-6xl mb-4">💬</div>

            <h3 className="text-xl font-semibold text-[#111827]">
              No Chat Selected
            </h3>

            <p className="text-gray-500 mt-2">
              Select a conversation from the left panel to view messages.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* HEADER */}
      <div className="h-[80px] border-b border-[#e7ebf3] px-6 flex items-center">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="w-10 h-10 rounded-xl border border-[#e7ebf3] hover:bg-[#f8fafc] flex items-center justify-center transition"
            >
              <ArrowLeft size={18} />
            </button>

            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center font-semibold text-green-700">
              {(
                selectedContact.customName ||
                selectedContact.name ||
                selectedContact.phone ||
                "?"
              )
                .charAt(0)
                .toUpperCase()}
            </div>

            <div>
              <h2 className="text-lg font-semibold text-[#111827]">
                {selectedContact.customName ||
                  selectedContact.name ||
                  "Unknown Contact"}
              </h2>

              <p className="text-sm text-gray-500">{selectedContact.phone}</p>
            </div>
          </div>

          <button
            onClick={() => {
              setCustomName(
                selectedContact.customName || selectedContact.name || "",
              );

              setShowRenameModal(true);
            }}
            className="w-10 h-10 rounded-xl border border-[#e7ebf3] hover:bg-[#f8fafc] flex items-center justify-center transition"
            title="Rename Contact"
          >
            <Pencil size={16} />
          </button>
        </div>
      </div>

      {/* MESSAGES */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto bg-[#f8fafc] p-5"
      >
        {loading ? (
          <div className="space-y-4">
            <div className="h-12 w-48 rounded-xl bg-gray-200 animate-pulse" />

            <div className="h-12 w-64 rounded-xl bg-gray-200 animate-pulse ml-auto" />

            <div className="h-12 w-40 rounded-xl bg-gray-200 animate-pulse" />
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500">No messages yet</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message._id}
                className={`flex ${
                  message.direction === "OUTBOUND"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[70%] px-4 py-3 rounded-2xl shadow-sm ${
                    message.direction === "OUTBOUND"
                      ? "bg-green-500 text-white"
                      : "bg-white border border-[#e7ebf3]"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">
                    {message.message}
                  </p>

                  {message.direction === "OUTBOUND" && (
                    <div className="flex justify-end mt-2">
                      {renderStatusIcon(message.status)}
                    </div>
                  )}
                </div>
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {showRenameModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-full max-w-md p-6 shadow-xl">
            <h3 className="text-xl font-semibold text-[#111827]">
              Rename Contact
            </h3>

            <p className="text-sm text-gray-500 mt-1">
              Set a custom name for this contact.
            </p>

            <input
              type="text"
              value={customName}
              onChange={(e) => setCustomName(e.target.value)}
              placeholder="Enter contact name"
              className="w-full mt-4 h-12 px-4 rounded-xl border border-[#e7ebf3] focus:outline-none focus:ring-2 focus:ring-green-500"
            />

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => {
                  setShowRenameModal(false);
                  setCustomName("");
                }}
                className="px-4 py-2 rounded-xl border border-[#e7ebf3]"
              >
                Cancel
              </button>

              <button
                onClick={handleRenameContact}
                className="px-4 py-2 rounded-xl bg-green-600 text-white hover:bg-green-700"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      <MessageInput
        selectedContact={selectedContact}
        onMessageSent={() => fetchChat(false)}
      />
    </div>
  );
}
