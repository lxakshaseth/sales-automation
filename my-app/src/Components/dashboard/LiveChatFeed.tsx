"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, Send } from "lucide-react";
import { motion } from "framer-motion";

interface ChatMessage {
  id: string;
  sender: "user" | "other";
  text: string;
  time: string;
  initials: string;
}

export default function LiveChatFeed() {
  const [inputValue, setInputValue] = useState("");

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      sender: "other",
      initials: "RS",
      text: "Hi there! I am interested in your Sales Automation tool. Can you explain how the WhatsApp campaign works?",
      time: "10:42 AM",
    },
    {
      id: "2",
      sender: "user",
      initials: "You",
      text: "Hello Rahul! 👋 Our WhatsApp campaigns allow you to send personalized messages to your leads directly. You can set up templates and schedule them.",
      time: "10:43 AM",
    },
    {
      id: "3",
      sender: "other",
      initials: "RS",
      text: "That sounds perfect! Are there any limits on how many messages I can send per day?",
      time: "10:45 AM",
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: "user",
      initials: "You",
      text: inputValue,
      time: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue("");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
className="bg-white border border-[#e5e7eb] rounded-[20px] shadow-sm overflow-hidden h-[420px] flex flex-col"    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#eef2f7] flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-[18px] font-semibold text-[#111827]">
          <MessageSquare
            size={18}
            className="text-[#3b82f6]"
          />
          Live Chat Feed
        </h3>

        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#eafaf0]">
          <span className="w-2 h-2 rounded-full bg-[#22c55e]" />
          <span className="text-[12px] font-medium text-[#16a34a]">
            Online
          </span>
        </div>
      </div>

      {/* Messages */}
     <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${
              msg.sender === "user"
                ? "justify-end"
                : "justify-start"
            }`}
          >
            {msg.sender !== "user" && (
              <div className="w-10 h-10 rounded-full bg-[#eadcff] text-[#7c3aed] flex items-center justify-center text-sm font-semibold shrink-0">
                {msg.initials}
              </div>
            )}

            <div
              className={`max-w-[70%] rounded-[18px] px-4 py-3 ${
                msg.sender === "user"
                  ? "bg-[#f4e8ff] text-[#374151]"
                  : "bg-white text-[#374151]"
              }`}
            >
              <p className="text-[14px] leading-6">
                {msg.text}
              </p>

              <p className="mt-2 text-[11px] text-[#94a3b8]">
                {msg.time}
              </p>
            </div>

            {msg.sender === "user" && (
              <div className="w-7 h-7 rounded-full bg-[#8b5cf6] text-white flex items-center justify-center text-[11px] font-medium shrink-0">
                You
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-[#eef2f7] p-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Type your message..."
            value={inputValue}
            onChange={(e) =>
              setInputValue(e.target.value)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter")
                handleSendMessage();
            }}
            className="w-full h-11 rounded-[12px] border border-[#e5e7eb] bg-white px-4 pr-14 text-[14px] outline-none focus:border-[#8b5cf6]"
          />

          <button
            onClick={handleSendMessage}
            className="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-[#8b5cf6] text-white flex items-center justify-center hover:bg-[#7c3aed] transition"
          >
            <Send size={15} />
          </button>
        </div>
      </div>
    </motion.div>
  );
}