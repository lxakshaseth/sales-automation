export interface Contact {
  _id: string;
  waId: string;
  name?: string; // The name of the contact as provided by WhatsApp
  customName?: string;
  phone?: string;
  aiEnabled?: boolean;
  lastMessage?: string;
  lastMessageDirection?: Message["direction"];
  lastMessageStatus?: Message["status"];
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

type ApiResponse<T> = {
  success: boolean;
  data: T;
  message?: string;
};

type ChatData = {
  contact: Contact;
  messages: Message[];
};

type SendMessageData = {
  whatsapp?: unknown;
  inboundMessage?: Message | null;
  outboundMessage?: Message | null;
};

export class WhatsAppApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "WhatsAppApiError";
    this.status = status;
    this.data = data;
  }
}

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

export function isNotFoundError(error: unknown) {
  return error instanceof WhatsAppApiError && error.status === 404;
}

async function readResponseData(response: Response) {
  const text = await response.text();

  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch {
    return {
      message: text,
    };
  }
}

async function readJsonResponse<T>(
  response: Response,
  fallbackMessage: string,
) {
  const data = (await readResponseData(response)) as T & {
    message?: string;
  };

  if (!response.ok) {
    throw new WhatsAppApiError(
      data.message || fallbackMessage,
      response.status,
      data,
    );
  }

  return data;
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

    return await readJsonResponse<ApiResponse<Contact[]>>(
      response,
      "Failed to fetch contacts",
    );
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
    const response = await fetch(
      `/api/whatsapp/contacts/${encodeURIComponent(contactId)}`,
      {
        method: "PATCH",
        headers: getAuthHeaders(),
        signal: request.signal,
        body: JSON.stringify({
          customName,
        }),
      },
    );

    return await readJsonResponse<ApiResponse<Contact>>(
      response,
      "Failed to update contact",
    );
  } catch (error) {
    if (!isNotFoundError(error)) {
      throw error;
    }

    const fallbackResponse = await fetch("/api/whatsapp/contacts", {
      method: "PATCH",
      headers: getAuthHeaders(),
      signal: request.signal,
      body: JSON.stringify({
        contactId,
        customName,
      }),
    });

    return await readJsonResponse<ApiResponse<Contact>>(
      fallbackResponse,
      "Failed to update contact",
    );
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
    const response = await fetch(
      `/api/whatsapp/contacts/${encodeURIComponent(contactId)}`,
      {
        method: "PATCH",
        headers: getAuthHeaders(),
        signal: request.signal,
        body: JSON.stringify({
          aiEnabled,
        }),
      },
    );

    return await readJsonResponse<ApiResponse<Contact>>(
      response,
      "Failed to update AI setting",
    );
  } catch (error) {
    if (!isNotFoundError(error)) {
      throw error;
    }

    const fallbackResponse = await fetch("/api/whatsapp/contacts", {
      method: "PATCH",
      headers: getAuthHeaders(),
      signal: request.signal,
      body: JSON.stringify({
        contactId,
        aiEnabled,
      }),
    });

    return await readJsonResponse<ApiResponse<Contact>>(
      fallbackResponse,
      "Failed to update AI setting",
    );
  } finally {
    request.cleanup();
  }
}

export async function getChatByWaId(waId: string, options?: RequestOptions) {
  const request = createRequestSignal(options);

  try {
    const response = await fetch(
      `/api/whatsapp/chat/${encodeURIComponent(waId)}`,
      {
        headers: getAuthHeaders(),
        signal: request.signal,
        cache: "no-store",
      },
    );

    return await readJsonResponse<ApiResponse<ChatData>>(
      response,
      "Failed to fetch chat",
    );
  } catch (error) {
    if (!isNotFoundError(error)) {
      throw error;
    }

    const fallbackResponse = await fetch(
      `/api/whatsapp/chat?waId=${encodeURIComponent(waId)}`,
      {
        headers: getAuthHeaders(),
        signal: request.signal,
        cache: "no-store",
      },
    );

    return await readJsonResponse<ApiResponse<ChatData>>(
      fallbackResponse,
      "Failed to fetch chat",
    );
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

  return await readJsonResponse<ApiResponse<SendMessageData>>(
    response,
    "Failed to send message",
  );
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

    return await readJsonResponse<{
      success: boolean;
      message?: string;
    }>(response, "Failed to mark chat as read");
  } finally {
    request.cleanup();
  }
}
