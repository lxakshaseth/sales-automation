"use client";

import { useState, useRef, useEffect } from "react";
import { MessageSquare, Send } from "lucide-react";

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
    { id: '1', sender: 'other', initials: 'JD', text: 'Hi there! I am interested in your Sales Automation tool. Can you explain how the WhatsApp campaign works?', time: '10:42 AM' },
    { id: '2', sender: 'user', initials: 'You', text: 'Hello! Absolutely. Our WhatsApp campaigns allow you to send personalized messages to your leads directly. You can set up templates and schedule them.', time: '10:43 AM' },
    { id: '3', sender: 'other', initials: 'AS', text: 'That sounds perfect! Are there any limits on how many messages I can send per day?', time: '10:45 AM' },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the bottom of the chat when a new message is added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: "user",
      initials: "You",
      text: inputValue.trim(),
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputValue("");
  };

  return (
    <div 
      className="xl:col-span-2 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm flex flex-col overflow-hidden h-112.5"
    >
      <div 
        className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between shrink-0"
      >
        <h3 className="font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
          <MessageSquare size={18} className="text-emerald-500" />
          Live Chat Feed
        </h3>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 dark:bg-emerald-500/10 px-2 py-1 rounded-full">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            Online
          </span>
        </div>
      </div>
      
      {/* Chat Messages */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4 scrollbar-thin scrollbar-thumb-zinc-200 dark:scrollbar-thumb-zinc-800">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex items-start gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-medium text-xs shrink-0 ${
              msg.sender === 'user' 
                ? 'bg-blue-600 text-white' 
                : msg.initials === 'JD' 
                  ? 'bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400' 
                  : 'bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400'
            }`}>
              {msg.initials}
            </div>
            <div className={`p-3 text-sm max-w-[80%] rounded-2xl ${
              msg.sender === 'user' 
                ? 'bg-blue-600 text-white rounded-tr-sm shadow-sm' 
                : 'bg-zinc-100 dark:bg-zinc-800/50 text-zinc-700 dark:text-zinc-300 rounded-tl-sm'
            }`}>
              {msg.text}
              <span className={`block text-[10px] mt-1.5 ${msg.sender === 'user' ? 'text-blue-200' : 'text-zinc-400'}`}>
                {msg.time}
              </span>
            </div>
          </div>
        ))}
        {/* Invisible div to target for auto-scrolling */}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50 rounded-b-2xl shrink-0">
        <div className="relative">
          <input type="text" placeholder="Type your message..." value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage() }} className="w-full bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-full pl-4 pr-12 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white shadow-sm" />
          <button onClick={handleSendMessage} className="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 flex items-center justify-center bg-blue-600 hover:bg-blue-700 text-white rounded-full transition-colors shadow-sm"><Send size={14} className="ml-0.5" /></button>
        </div>
      </div>
    </div>
  );
}