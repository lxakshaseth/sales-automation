"use client";

import { useState } from "react";

import { Send } from "lucide-react";

import {
  Contact,
  sendMessage,
} from "@/services/whatsapp.service";

type MessageInputProps = {
  selectedContact: Contact;
  onMessageSent: (
    data: Awaited<ReturnType<typeof sendMessage>>["data"],
  ) => Promise<void> | void;
  onSendingChange?: (sending: boolean) => void;
};

export default function MessageInput({
  selectedContact,
  onMessageSent,
  onSendingChange,
}: MessageInputProps) {
  const [message, setMessage] =
    useState("");

  const [sending, setSending] =
    useState(false);

  async function handleSend() {
    const cleanMessage = message.trim();

    if (sending || !cleanMessage) return;

    try {
      setSending(true);
      onSendingChange?.(true);

      const response = await sendMessage({
        to: selectedContact.waId,
        message: cleanMessage,
      });

      setMessage("");

      await onMessageSent(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setSending(false);
      onSendingChange?.(false);
    }
  }

  async function handleKeyDown(
    e: React.KeyboardEvent<HTMLInputElement>,
  ) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      await handleSend();
    }
  }

  return (
    <div className="shrink-0 border-t border-[#e7ebf3] p-4 bg-white">

      <div className="flex gap-3">

        <input
          type="text"
          value={message}
          onChange={(e) =>
            setMessage(e.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          disabled={sending}
          className="flex-1 h-12 px-4 rounded-xl border border-[#e7ebf3] focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
        />

        <button
          onClick={handleSend}
          disabled={
            sending || !message.trim()
          }
          className="h-12 px-5 rounded-xl bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white flex items-center gap-2 transition"
        >
          <Send size={18} />

          {sending
            ? "Sending..."
            : "Send"}
        </button>

      </div>

    </div>
  );
}
