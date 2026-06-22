export interface Contact {
  _id: string;
  waId: string;
  name?: string;
  customName?: string;
  phone?: string;
  aiEnabled?: boolean;
  lastMessage?: string;
  lastMessageDirection?: Message["direction"];
  lastMessageCreatedAt?: string;
  unreadCount?: number;
  lastMessageAt: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  _id: string;
  contactId: string;
  waMessageId: string;
  direction: "INBOUND" | "OUTBOUND";
  type: "text" | "template";
  message: string;
  status?: "RECEIVED" | "SENT" | "DELIVERED" | "READ" | "FAILED";
  createdAt: string;
  updatedAt: string;
}

type RequestOptions = {
  signal?: AbortSignal;
  timeoutMs?: number;
};

function getAuthHeaders() {
  const token = sessionStorage.getItem("token");

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function createRequestSignal({ signal, timeoutMs }: RequestOptions = {}) {
  if (!timeoutMs) {
    return {
      signal,
      cleanup: () => {},
    };
  }

  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

  const abortFromParent = () => controller.abort();

  if (signal?.aborted) {
    controller.abort();
  } else {
    signal?.addEventListener("abort", abortFromParent, {
      once: true,
    });
  }

  return {
    signal: controller.signal,
    cleanup: () => {
      window.clearTimeout(timeout);
      signal?.removeEventListener("abort", abortFromParent);
    },
  };
}

export async function getContacts(options?: RequestOptions) {
  const request = createRequestSignal(options);

  try {
    const response = await fetch("/api/whatsapp/contacts", {
      headers: getAuthHeaders(),
      signal: request.signal,
      cache: "no-store",
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to fetch contacts");
    }

    return data;
  } finally {
    request.cleanup();
  }
}

export async function updateContactName(
  contactId: string,
  customName: string,
  options?: RequestOptions,
) {
  const request = createRequestSignal(options);

  try {
    const response = await fetch(`/api/whatsapp/contacts/${contactId}`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      signal: request.signal,
      body: JSON.stringify({
        customName,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to update contact");
    }

    return data;
  } finally {
    request.cleanup();
  }
}

export async function updateContactAiEnabled(
  contactId: string,
  aiEnabled: boolean,
  options?: RequestOptions,
) {
  const request = createRequestSignal(options);

  try {
    const response = await fetch(`/api/whatsapp/contacts/${contactId}`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      signal: request.signal,
      body: JSON.stringify({
        aiEnabled,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to update AI setting");
    }

    return data;
  } finally {
    request.cleanup();
  }
}

export async function getChatByWaId(waId: string, options?: RequestOptions) {
  const request = createRequestSignal(options);

  try {
    const response = await fetch(`/api/whatsapp/chat/${waId}`, {
      headers: getAuthHeaders(),
      signal: request.signal,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to fetch chat");
    }

    return data;
  } finally {
    request.cleanup();
  }
}

export async function sendMessage({
  to,
  message,
}: {
  to: string;
  message: string;
}) {
  const response = await fetch("/api/whatsapp/send", {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      to,
      message,
    }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Failed to send message");
  }

  return data;
}

export async function markChatAsRead(waId: string, options?: RequestOptions) {
  const request = createRequestSignal(options);

  try {
    const response = await fetch("/api/whatsapp/chat/read", {
      method: "POST",
      headers: getAuthHeaders(),
      signal: request.signal,
      body: JSON.stringify({
        waId,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || "Failed to mark chat as read");
    }

    return data;
  } finally {
    request.cleanup();
  }
}
