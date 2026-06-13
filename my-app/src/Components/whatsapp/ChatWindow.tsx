"use client";

import {
  useEffect,
  useState,
  useRef,
} from "react";

import {
  ArrowLeft,
  Check,
  CheckCheck,
} from "lucide-react";

import MessageInput from "./MessageInput";

import {
  Contact,
  Message,
  getChatByWaId,
} from "@/services/whatsapp.service";

type ChatWindowProps = {
  selectedContact: Contact | null;
  onBack: () => void;
};

export default function ChatWindow({
  selectedContact,
  onBack,
}: ChatWindowProps) {
  const [messages, setMessages] =
    useState<Message[]>([]);

  const [loading, setLoading] =
    useState(false);

  const messagesEndRef =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!selectedContact) return;

    fetchChat();
  }, [selectedContact]);

  useEffect(() => {
    if (!selectedContact) return;

    const interval = setInterval(() => {
      fetchChat(false);
    }, 3000);

    return () =>
      clearInterval(interval);
  }, [selectedContact]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function fetchChat(
    showLoader = true,
  ) {
    if (!selectedContact) return;

    try {
      if (showLoader) {
        setLoading(true);
      }

      const response =
        await getChatByWaId(
          selectedContact.waId,
        );

      setMessages(
        response.data?.messages || [],
      );
    } catch (error) {
      console.error(error);
    } finally {
      if (showLoader) {
        setLoading(false);
      }
    }
  }

  function renderStatusIcon(
    status?: string,
  ) {
    switch (status) {
      case "SENT":
        return (
          <Check
            size={14}
            className="inline"
          />
        );

      case "DELIVERED":
        return (
          <CheckCheck
            size={14}
            className="inline"
          />
        );

      case "READ":
        return (
          <CheckCheck
            size={14}
            className="inline text-blue-300"
          />
        );

      case "FAILED":
        return (
          <span className="text-red-300">
            ❌
          </span>
        );

      default:
        return null;
    }
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

            <div className="text-6xl mb-4">
              💬
            </div>

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

        <div className="flex items-center gap-4">

          <button
            onClick={onBack}
            className="w-10 h-10 rounded-xl border border-[#e7ebf3] hover:bg-[#f8fafc] flex items-center justify-center transition"
          >
            <ArrowLeft size={18} />
          </button>

          <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center font-semibold text-green-700">
            {(selectedContact.name ||
              selectedContact.phone ||
              "?")
              .charAt(0)
              .toUpperCase()}
          </div>

          <div>
            <h2 className="text-lg font-semibold text-[#111827]">
              {selectedContact.name ||
                "Unknown Contact"}
            </h2>

            <p className="text-sm text-gray-500">
              {selectedContact.phone}
            </p>
          </div>

        </div>

      </div>

      {/* MESSAGES */}
      <div className="flex-1 overflow-y-auto bg-[#f8fafc] p-5">

        {loading ? (
          <div className="space-y-4">

            <div className="h-12 w-48 rounded-xl bg-gray-200 animate-pulse" />

            <div className="h-12 w-64 rounded-xl bg-gray-200 animate-pulse ml-auto" />

            <div className="h-12 w-40 rounded-xl bg-gray-200 animate-pulse" />

          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500">
              No messages yet
            </p>
          </div>
        ) : (
          <div className="space-y-4">

            {messages.map((message) => (
              <div
                key={message._id}
                className={`flex ${
                  message.direction ===
                  "OUTBOUND"
                    ? "justify-end"
                    : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[70%] px-4 py-3 rounded-2xl shadow-sm ${
                    message.direction ===
                    "OUTBOUND"
                      ? "bg-green-500 text-white"
                      : "bg-white border border-[#e7ebf3]"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">
                    {message.message}
                  </p>

                  {message.direction ===
                    "OUTBOUND" && (
                    <div className="flex justify-end mt-2">
                      {renderStatusIcon(
                        message.status,
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}

            <div ref={messagesEndRef} />

          </div>
        )}

      </div>

      <MessageInput
        selectedContact={selectedContact}
        onMessageSent={() =>
          fetchChat(false)
        }
      />

    </div>
  );
}