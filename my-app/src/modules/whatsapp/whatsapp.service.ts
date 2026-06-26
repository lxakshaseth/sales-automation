import mongoose from "mongoose";

import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import Message from "@/modules/whatsapp/message.model";

const OUTBOUND_STATUS_RANK = {
  SENT: 1,
  DELIVERED: 2,
  READ: 3,
} as const;

type OutboundProgressStatus = keyof typeof OUTBOUND_STATUS_RANK;
type MessageStatus =
  | OutboundProgressStatus
  | "FAILED"
  | "RECEIVED";

function getUnreadCustomerMessageFilter(contactId: unknown) {
  return {
    contactId,
    direction: "INBOUND",
    status: "RECEIVED",
    "rawPayload.entry.0.changes.0.value.messages.0.type": {
      $ne: "system",
    },
  };
}

function getWhatsAppMessageId(rawPayload: unknown) {
  if (
    rawPayload &&
    typeof rawPayload === "object" &&
    "messages" in rawPayload
  ) {
    const messages = (rawPayload as { messages?: { id?: string }[] }).messages;

    return messages?.[0]?.id;
  }
}

function getContactIdentifierVariants(identifier: string) {
  const trimmed = decodeURIComponent(identifier).trim();
  const withoutWhatsappPrefix = trimmed.replace(/^whatsapp:/i, "");
  const withoutPlus = withoutWhatsappPrefix.replace(/^\+/, "");

  return Array.from(
    new Set([
      trimmed,
      withoutWhatsappPrefix,
      withoutPlus,
      `+${withoutPlus}`,
      `whatsapp:${withoutWhatsappPrefix}`,
      `whatsapp:+${withoutPlus}`,
    ].filter(Boolean)),
  );
}

function getContactLookupFilter(identifier: string) {
  const variants = getContactIdentifierVariants(identifier);
  const filters: Record<string, unknown>[] = [
    {
      waId: {
        $in: variants,
      },
    },
    {
      phone: {
        $in: variants,
      },
    },
  ];

  if (mongoose.Types.ObjectId.isValid(identifier)) {
    filters.unshift({
      _id: identifier,
    });
  }

  return {
    $or: filters,
  };
}

function normalizeMessageStatus(status: string): MessageStatus | null {
  const normalizedStatus = status.toUpperCase();

  if (
    normalizedStatus === "SENT" ||
    normalizedStatus === "DELIVERED" ||
    normalizedStatus === "READ" ||
    normalizedStatus === "FAILED" ||
    normalizedStatus === "RECEIVED"
  ) {
    return normalizedStatus;
  }

  return null;
}

function getUpdatableOutboundStatuses(nextStatus: MessageStatus) {
  if (nextStatus === "FAILED") {
    return ["SENT", "DELIVERED", "FAILED"];
  }

  if (!(nextStatus in OUTBOUND_STATUS_RANK)) {
    return [];
  }

  const nextRank = OUTBOUND_STATUS_RANK[nextStatus as OutboundProgressStatus];

  return Object.entries(OUTBOUND_STATUS_RANK)
    .filter(([, rank]) => rank <= nextRank)
    .map(([status]) => status);
}

export async function upsertContact({
  waId,
  name,
  phone,   //phone number of the contact
}: {
  waId: string;
  name?: string;
  phone?: string;
}) {
  await connectDB();

  const existing = await Contact.findOne({ waId });

  if (existing) {
    if (name) {
      existing.name = name;
    }

    existing.lastMessageAt = new Date();

    await existing.save();

    return existing;
  }

  return await Contact.create({
    waId,
    name,
    phone,
    lastMessageAt: new Date(),
  });
}

export async function saveInboundMessage({
  contactId,
  waMessageId,
  message,
  rawPayload,
}: {
  contactId: string;
  waMessageId: string;
  message: string;
  rawPayload: unknown;
}) {
  await connectDB();

  const existingMessage = await Message.findOne({
    waMessageId,
  });

  if (existingMessage) {
    return existingMessage;
  }

  return await Message.create({
    contactId,
    waMessageId,
    message,
    direction: "INBOUND",
    type: "text",
    rawPayload,
    status: "RECEIVED",
  });
}

export async function messageExistsByWaMessageId(waMessageId: string) {
  await connectDB();

  return Boolean(
    await Message.exists({
      waMessageId,
    }),
  );
}

export async function saveOutboundMessage({
  contactId,
  waMessageId,
  message,
  rawPayload,
}: {
  contactId: string;
  waMessageId: string;
  message: string;
  rawPayload: unknown;
}) {
  await connectDB();

  const messageId = waMessageId || getWhatsAppMessageId(rawPayload);

  const outboundMessage = await Message.create({
    contactId,
    waMessageId: messageId,
    message,
    direction: "OUTBOUND",
    type: "text",
    rawPayload,
    status: "SENT",
  });

  await Contact.findByIdAndUpdate(contactId, {
    lastMessageAt: new Date(),
  });

  return outboundMessage;
}

export async function sendWhatsAppTextMessage({
  to,
  message,
}: {
  to: string;
  message: string;
}) {
  const response = await fetch(
    `https://graph.facebook.com/v25.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.WHATSAPP_ACCESS_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messaging_product: "whatsapp",
        recipient_type: "individual",
        to,
        type: "text",
        text: { body: message },
      }),
    },
  );

  const data = await response.json();

  return {
    ok: response.ok,
    status: response.status,
    data,
  };
}

export async function updateMessageStatus({
  waMessageId,
  status,
}: {
  waMessageId: string;
  status: string;
}) {
  await connectDB();

  const normalizedStatus = normalizeMessageStatus(status);

  if (!normalizedStatus) {
    return null;
  }

  const updatableStatuses = getUpdatableOutboundStatuses(normalizedStatus);

  if (!updatableStatuses.length) {
    return null;
  }

  const result = await Message.updateOne(
    {
      direction: "OUTBOUND",
      status: {
        $in: updatableStatuses,
      },
      $or: [
        {
          waMessageId,
        },
        {
          "rawPayload.messages.id": waMessageId,
        },
      ],
    },
    {
      $set: {
        status: normalizedStatus,
      },
    },
  );

  return result;
}

export async function getChatByWaId(waId: string) {
  await connectDB();

  const contact = await Contact.findOne(getContactLookupFilter(waId));

  if (!contact) return null;

  const messages = await Message.find({
    contactId: contact._id,
  }).sort({ createdAt: 1 });

  return {
    contact,
    messages,
  };
}

export async function getContacts() {
  await connectDB();

  const contacts = await Contact.find().sort({
    lastMessageAt: -1,
  });

  return Promise.all(
    contacts.map(async (contact) => {
      const [lastMessage, unreadCount] = await Promise.all([
        Message.findOne({
          contactId: contact._id,
        })
          .sort({ createdAt: -1 })
          .lean(),
        Message.countDocuments({
          ...getUnreadCustomerMessageFilter(contact._id),
        }),
      ]);

      const visibleUnreadCount =
        lastMessage?.direction === "INBOUND" ? unreadCount : 0;

      return {
        ...contact.toObject(),
        lastMessage: lastMessage?.message || "",
        lastMessageDirection: lastMessage?.direction,
        lastMessageStatus: lastMessage?.status,
        lastMessageCreatedAt: lastMessage?.createdAt,
        unreadCount: visibleUnreadCount,
      };
    }),
  );
}

export async function markMessagesAsRead(waId: string) {
  await connectDB();

  const contact = await Contact.findOne(getContactLookupFilter(waId));

  if (!contact) return;

  const unreadMessages = await Message.find({
    ...getUnreadCustomerMessageFilter(contact._id),
  });

  for (const msg of unreadMessages) {
    try {
      let readReceiptConfirmed = true;

      if (
        process.env.WHATSAPP_ACCESS_TOKEN &&
        process.env.WHATSAPP_PHONE_NUMBER_ID
      ) {
        readReceiptConfirmed = false;

        const response = await fetch(
          `https://graph.facebook.com/v25.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${process.env.WHATSAPP_ACCESS_TOKEN}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              messaging_product: "whatsapp",
              status: "read",
              message_id: msg.waMessageId,
            }),
          },
        );

        if (!response.ok) {
          const body = await response.text().catch(() => "");

          console.warn("[whatsapp:read] Graph read receipt failed", {
            status: response.status,
            body,
            waMessageId: msg.waMessageId,
          });

          continue;
        }

        readReceiptConfirmed = true;
      }

      if (!readReceiptConfirmed) {
        continue;
      }

      msg.status = "READ";

      await msg.save();
    } catch (error) {
      console.error("Failed to mark message as read", error);
    }
  }
}

export async function updateContactName(contactId: string, customName: string) {
  await connectDB();

  return Contact.findOneAndUpdate(
    getContactLookupFilter(contactId),
    {
      customName,
    },
    {
      new: true,
    },
  );
}

export async function updateContactAiEnabled(
  contactId: string,
  aiEnabled: boolean,
) {
  await connectDB();

  return Contact.findOneAndUpdate(
    getContactLookupFilter(contactId),
    {
      aiEnabled,
    },
    {
      new: true,
    },
  );
}
