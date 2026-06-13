export interface Contact {
  _id: string;
  waId: string;
  name?: string;
  phone?: string;
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
  status?: "SENT" | "DELIVERED" | "READ" | "FAILED";
  createdAt: string;
  updatedAt: string;
}

function getAuthHeaders() {
  const token = sessionStorage.getItem(
    "token",
  );

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function getContacts() {
  const response = await fetch(
    "/api/whatsapp/contacts",
    {
      headers: getAuthHeaders(),
    },
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.message ||
        "Failed to fetch contacts",
    );
  }

  return data;
}

export async function getChatByWaId(
  waId: string,
) {
  const response = await fetch(
    `/api/whatsapp/chat/${waId}`,
    {
      headers: getAuthHeaders(),
    },
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.message ||
        "Failed to fetch chat",
    );
  }

  return data;
}

export async function sendMessage({
  to,
  message,
}: {
  to: string;
  message: string;
}) {
  const response = await fetch(
    "/api/whatsapp/send",
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        to,
        message,
      }),
    },
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.message ||
        "Failed to send message",
    );
  }

  return data;
}