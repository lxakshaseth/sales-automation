"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  ArrowLeft,
  Bot, // This is the Bot icon from lucide-react
  Check,
  CheckCheck,
  MessageCircle,
  Pencil,
  XCircle,
} from "lucide-react";

import MessageInput from "./MessageInput";

import {
  Contact,
  Message,
  getChatByWaId,
  isAbortError,
  markChatAsRead,
  updateContactAiEnabled,
  updateContactName,
} from "@/services/whatsapp.service";


type ChatWindowProps = {
  selectedContact: Contact | null;
  onBack: () => void;
  onContactUpdated: (contact: Contact) => void;
  onChatRead?: (waId: string) => void;
};

type ChatDisplayMessage = {
  id: string;
  sender: "user" | "ai";
  text: string;
  timestamp: string;
  status?: Message["status"];
};

const CHAT_POLL_INTERVAL_MS = 6000;

function getMessageSnapshot(message: Message) {
  return [
    message._id,
    message.waMessageId,
    message.direction,
    message.type,
    message.message,
    message.status || "",
    message.createdAt,
    message.updatedAt,
  ].join("\u0001");
}

function areMessagesSame(
  currentMessages: Message[],
  nextMessages: Message[],
) {
  return (
    currentMessages.length === nextMessages.length &&
    currentMessages.every(
      (message, index) =>
        getMessageSnapshot(message) === getMessageSnapshot(nextMessages[index]),
    )
  );
}

export default function ChatWindow({
  selectedContact,
  onBack,
  onContactUpdated,
  onChatRead,
}: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [customName, setCustomName] = useState("");
  const [assistantReplying, setAssistantReplying] = useState(false);
  const [aiToggleSaving, setAiToggleSaving] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const shouldAutoScrollRef = useRef(true);
  const previousMessageCountRef = useRef(0);
  const mountedRef = useRef(false);
  const chatAbortControllerRef = useRef<AbortController | null>(null);
  const chatInFlightRef = useRef(false);
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const readAbortControllerRef = useRef<AbortController | null>(null);
  const readInFlightRef = useRef(false);
  const lastReadKeyRef = useRef("");

  const clearPollTimer = useCallback(() => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const abortChatRequest = useCallback(() => {
    chatAbortControllerRef.current?.abort();
    chatAbortControllerRef.current = null;
    chatInFlightRef.current = false;
  }, []);

  const abortReadRequest = useCallback(() => {
    readAbortControllerRef.current?.abort();
    readAbortControllerRef.current = null;
    readInFlightRef.current = false;
  }, []);

  const fetchChat = useCallback(
    async (showLoader = false) => {
      if (!selectedContact) return;

      if (chatInFlightRef.current) {
        console.info("[whatsapp:chat] request:skipped", {
          reason: "chat request already in progress",
          waId: selectedContact.waId,
        });

        return;
      }

      const waId = selectedContact.waId;
      const controller = new AbortController();

      chatAbortControllerRef.current = controller;
      chatInFlightRef.current = true;

      console.info("[whatsapp:chat] fetch:start", {
        showLoader,
        waId,
      });

      try {
        if (showLoader && mountedRef.current) {
          setLoading(true);
        }

        const response = await getChatByWaId(waId, {
          signal: controller.signal,
          timeoutMs: 30000,
        });

        if (
          !mountedRef.current ||
          controller.signal.aborted ||
          selectedContact.waId !== waId
        ) {
          return;
        }

        const nextMessages = response.data?.messages || [];

        setMessages((currentMessages) =>
          areMessagesSame(currentMessages, nextMessages)
            ? currentMessages
            : nextMessages,
        );
        setErrorMessage("");

        console.info("[whatsapp:chat] fetch:success", {
          waId,
          count: response.data?.messages?.length || 0,
        });

        if (showLoader) {
          setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({
              behavior: "auto",
            });
          }, 100);
        }
      } catch (error) {
        if (isAbortError(error)) {
          console.info("[whatsapp:chat] fetch:aborted", {
            waId,
          });

          return;
        }

        console.error("[whatsapp:chat] fetch:failure", {
          waId,
          error,
        });

        if (mountedRef.current) {
          setErrorMessage("Unable to refresh chat. Retrying shortly.");
        }
      } finally {
        if (chatAbortControllerRef.current === controller) {
          chatAbortControllerRef.current = null;
        }

        chatInFlightRef.current = false;

        if (showLoader && mountedRef.current) {
          setLoading(false);
        }
      }
    },
    [selectedContact],
  );

  const markReadIfNeeded = useCallback(async () => {
    if (!selectedContact || readInFlightRef.current) {
      return;
    }

    const unreadCount = messages.filter(
      (message) =>
        message.direction === "INBOUND" && message.status === "RECEIVED",
    ).length;

    if (unreadCount === 0) {
      return;
    }

    const waId = selectedContact.waId;
    const readKey = `${waId}:${messages[messages.length - 1]?._id}:${unreadCount}`;

    if (lastReadKeyRef.current === readKey) {
      return;
    }

    const controller = new AbortController();

    readAbortControllerRef.current = controller;
    readInFlightRef.current = true;
    lastReadKeyRef.current = readKey;

    console.info("[whatsapp:chat] read:start", {
      waId,
      unreadCount,
    });

    try {
      await markChatAsRead(waId, {
        signal: controller.signal,
        timeoutMs: 15000,
      });

      console.info("[whatsapp:chat] read:success", {
        waId,
      });

      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.direction === "INBOUND" && message.status === "RECEIVED"
            ? {
                ...message,
                status: "READ",
              }
            : message,
        ),
      );
      onChatRead?.(waId);
    } catch (error) {
      if (isAbortError(error)) {
        console.info("[whatsapp:chat] read:aborted", {
          waId,
        });

        return;
      }

      lastReadKeyRef.current = "";

      console.warn("[whatsapp:chat] read:failure", {
        waId,
        error,
      });
    } finally {
      if (readAbortControllerRef.current === controller) {
        readAbortControllerRef.current = null;
      }

      readInFlightRef.current = false;
    }
  }, [messages, onChatRead, selectedContact]);

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;
      clearPollTimer();
      abortChatRequest();
      abortReadRequest();
    };
  }, [abortChatRequest, abortReadRequest, clearPollTimer]);

  useEffect(() => {
    clearPollTimer();
    abortChatRequest();
    abortReadRequest();
    lastReadKeyRef.current = "";
    previousMessageCountRef.current = 0;

    void Promise.resolve().then(() => {
      if (!mountedRef.current) {
        return;
      }

      setMessages([]);
      setErrorMessage("");
      setAssistantReplying(false);
      setAiToggleSaving(false);

      if (!selectedContact) {
        setLoading(false);
      }
    });

    if (!selectedContact) {
      return;
    }

    const poll = async (showLoader = false) => {
      await fetchChat(showLoader);

      if (!mountedRef.current || !selectedContact) {
        return;
      }

      pollTimerRef.current = setTimeout(
        () => void poll(false),
        CHAT_POLL_INTERVAL_MS,
      );
    };

    void Promise.resolve().then(() => poll(true));

    return () => {
      clearPollTimer();
      abortChatRequest();
      abortReadRequest();
    };
  }, [
    abortChatRequest,
    abortReadRequest,
    clearPollTimer,
    fetchChat,
    selectedContact,
  ]);

  useEffect(() => {
    void Promise.resolve().then(() => markReadIfNeeded());
  }, [markReadIfNeeded]);

  useEffect(() => {
    const container = messagesContainerRef.current;

    if (!container || !selectedContact) {
      return;
    }

    const handleScrollRead = () => {
      void markReadIfNeeded();
    };

    container.addEventListener("scroll", handleScrollRead);

    return () => {
      container.removeEventListener("scroll", handleScrollRead);
    };
  }, [markReadIfNeeded, selectedContact]);

  useEffect(() => {
    const hasNewMessage = messages.length > previousMessageCountRef.current;

    if ((hasNewMessage || assistantReplying) && shouldAutoScrollRef.current) {
      messagesEndRef.current?.scrollIntoView({
        behavior: "smooth",
      });
    }

    previousMessageCountRef.current = messages.length;
  }, [assistantReplying, messages]);

  async function handleRenameContact() {
    if (!selectedContact || !customName.trim()) {
      return;
    }

    const controller = new AbortController();

    try {
      const response = await updateContactName(
        selectedContact._id,
        customName.trim(),
        {
          signal: controller.signal,
          timeoutMs: 15000,
        },
      );

      onContactUpdated(response.data);
      setShowRenameModal(false);
      setCustomName("");
    } catch (error) {
      if (!isAbortError(error)) {
        console.error("[whatsapp:chat] rename:failure", {
          contactId: selectedContact._id,
          error,
        });
      }
    }
  }

  async function handleAiToggle() {
    if (!selectedContact || aiToggleSaving) {
      return;
    }

    const nextAiEnabled = !selectedContact.aiEnabled;
    const controller = new AbortController();

    try {
      setAiToggleSaving(true);

      const response = await updateContactAiEnabled(
        selectedContact._id,
        nextAiEnabled,
        {
          signal: controller.signal,
          timeoutMs: 15000,
        },
      );

      onContactUpdated(response.data);
    } catch (error) {
      if (!isAbortError(error)) {
        console.error("[whatsapp:chat] ai-toggle:failure", {
          contactId: selectedContact._id,
          error,
        });

        setErrorMessage("Unable to update AI mode. Please try again.");
      }
    } finally {
      setAiToggleSaving(false);
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
        return <XCircle size={14} className="inline text-red-300" />;

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

  function getDateKey(date: string) {
    const value = new Date(date);

    return `${value.getFullYear()}-${value.getMonth()}-${value.getDate()}`;
  }

  function formatDateSeparator(date: string) {
    const value = new Date(date);
    const today = new Date();
    const yesterday = new Date();

    yesterday.setDate(today.getDate() - 1);

    if (getDateKey(date) === getDateKey(today.toISOString())) {
      return "Today";
    }

    if (getDateKey(date) === getDateKey(yesterday.toISOString())) {
      return "Yesterday";
    }

    return value.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function formatMessageTime(date: string) {
    return new Date(date)
      .toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      })
      .toUpperCase();
  }

  const displayMessages = useMemo(
    () =>
      messages.map(
        (message): ChatDisplayMessage => ({
          id: message._id,
          sender: message.direction === "OUTBOUND" ? "ai" : "user",
          text: message.message,
          timestamp: message.createdAt,
          status: message.status,
        }),
      ),
    [messages],
  );

  function isSavedMessage(message: Message | null | undefined): message is Message {
    return Boolean(message?._id);
  }

  async function handleMessageSent(data: {
    inboundMessage?: Message;
    outboundMessage?: Message;
  }) {
    setMessages((currentMessages) => {
      const nextMessages = [
        ...currentMessages,
        data.inboundMessage,
        data.outboundMessage,
      ].filter(isSavedMessage);
      const messagesById = new Map<string, Message>();

      for (const message of nextMessages) {
        messagesById.set(message._id, message);
      }

      return Array.from(messagesById.values()).sort(
        (first, second) =>
          new Date(first.createdAt).getTime() -
          new Date(second.createdAt).getTime(),
      );
    });

    await fetchChat(false);
  }

  function renderTypingIndicator() {
    return (
      <div className="flex justify-end">
        <div className="max-w-[70%] rounded-2xl bg-green-500 px-4 py-3 text-sm text-white shadow-sm">
          <div className="flex items-center gap-2">
            <span>Replying</span>
            <span className="flex gap-1" aria-hidden="true">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/80" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/80 [animation-delay:120ms]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-white/80 [animation-delay:240ms]" />
            </span>
          </div>
        </div>
      </div>
    );
  }

  function renderMessageTime(message: ChatDisplayMessage) {
    return (
      <div
        className={`mt-2 flex items-center gap-1 text-[11px] ${
          message.sender === "ai"
            ? "justify-end text-white/80"
            : "justify-start text-gray-400"
        }`}
        title={new Date(message.timestamp).toLocaleString("en-IN", {
          weekday: "long",
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "numeric",
          minute: "2-digit",
        })}
      >
        <span>{formatMessageTime(message.timestamp)}</span>

        {message.sender === "ai" && renderStatusIcon(message.status)}
      </div>
    );
  }

  function getMessageDateKey(message: ChatDisplayMessage) {
    return getDateKey(message.timestamp);
  }

  function renderMessage(message: ChatDisplayMessage) {
    return (
      <div
        className={`flex ${
          message.sender === "ai" ? "justify-end" : "justify-start"
        }`}
      >
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-3 shadow-sm ${
            message.sender === "ai"
              ? "bg-green-500 text-white"
              : "border border-[#e7ebf3] bg-white"
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.text}</p>

          {renderMessageTime(message)}
        </div>
      </div>
    );
  }

  function renderDateSeparator(timestamp: string) {
    return (
      <div className="sticky top-2 z-10 flex justify-center">
        <span className="rounded-lg bg-white/90 px-3 py-1 text-xs font-medium text-gray-500 shadow-sm ring-1 ring-gray-200 backdrop-blur">
          {formatDateSeparator(timestamp)}
        </span>
      </div>
    );
  }

  function renderMessages() {
    return (
      <div className="space-y-4">
        {displayMessages.map((message, index) => {
          const previousMessage = displayMessages[index - 1];
          const showDateSeparator =
            !previousMessage ||
            getMessageDateKey(previousMessage) !== getMessageDateKey(message);

          return (
            <div key={message.id} className="space-y-4">
              {showDateSeparator && renderDateSeparator(message.timestamp)}

              {renderMessage(message)}
            </div>
          );
        })}

        {assistantReplying && renderTypingIndicator()}

        <div ref={messagesEndRef} />
      </div>
    );
  }

  function hasVisibleConversation() {
    return displayMessages.length > 0 || assistantReplying;
  }

  function handleSendingChange(isSending: boolean) {
    setAssistantReplying(isSending);
  }

  if (!selectedContact) {
    return (
      <div className="flex h-full min-h-0 flex-col">
        <div className="h-[80px] shrink-0 border-b border-[#e7ebf3] px-6 flex items-center">
          <div>
            <h2 className="text-lg font-semibold text-[#111827]">
              Select a Conversation
            </h2>

            <p className="text-sm text-gray-500">
              Choose a contact to start chatting
            </p>
          </div>
        </div>

        <div className="min-h-0 flex-1 bg-[#f8fafc] flex items-center justify-center">
          <div className="text-center max-w-sm">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-green-100 text-green-600">
              <MessageCircle size={30} />
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

  const aiOwnsConversation = Boolean(selectedContact.aiEnabled);

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="h-[80px] shrink-0 border-b border-[#e7ebf3] px-6 flex items-center">
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

            <div className="min-w-0">
              <h2 className="truncate text-lg font-semibold text-[#111827]">
                {selectedContact.customName ||
                  selectedContact.name ||
                  "Unknown Contact"}
              </h2>

              <div className="mt-1 flex flex-wrap items-center gap-2">
                <p className="text-sm text-gray-500">{selectedContact.phone}</p>

                {aiOwnsConversation && (
                  <span className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-green-200 bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                    <Bot size={13} />
                    <span className="truncate">
                      AI Assistant is actively responding to this customer
                    </span>
                  </span>
                )}
              </div>
            </div>
          </div>

          <button
            type="button"
            role="switch"
            aria-checked={Boolean(selectedContact.aiEnabled)}
            disabled={aiToggleSaving}
            onClick={handleAiToggle}
            className={`flex h-11 min-w-[154px] items-center justify-between gap-3 rounded-xl border px-3 text-sm font-semibold transition ${
              selectedContact.aiEnabled
                ? "border-green-200 bg-green-50 text-green-700"
                : "border-[#e7ebf3] bg-white text-gray-600 hover:bg-[#f8fafc]"
            } ${aiToggleSaving ? "cursor-not-allowed opacity-70" : ""}`}
            title={
              selectedContact.aiEnabled
                ? "AI is replying to this customer"
                : "Human will reply manually"
            }
          >
            <span className="flex items-center gap-2">
              <Bot size={17} />
              {selectedContact.aiEnabled ? "AI Enabled" : "AI Disabled"}
            </span>

            <span
              className={`relative h-5 w-9 rounded-full transition ${
                selectedContact.aiEnabled ? "bg-green-500" : "bg-gray-300"
              }`}
              aria-hidden="true"
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition ${
                  selectedContact.aiEnabled ? "left-4" : "left-0.5"
                }`}
              />
            </span>
          </button>

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

      {errorMessage && (
        <div className="shrink-0 border-b border-red-100 bg-red-50 px-5 py-2 text-sm text-red-600">
          {errorMessage}
        </div>
      )}

      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="min-h-0 flex-1 overflow-y-auto bg-[#f8fafc] p-5"
      >
        {loading ? (
          <div className="space-y-4">
            <div className="h-12 w-48 rounded-xl bg-gray-200 animate-pulse" />
            <div className="h-12 w-64 rounded-xl bg-gray-200 animate-pulse ml-auto" />
            <div className="h-12 w-40 rounded-xl bg-gray-200 animate-pulse" />
          </div>
        ) : !hasVisibleConversation() ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500">No messages yet</p>
          </div>
        ) : (
          renderMessages()
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
              onChange={(event) => setCustomName(event.target.value)}
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
        onMessageSent={handleMessageSent}
        onSendingChange={handleSendingChange}
      />
    </div>
  );
}
