import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import Message from "@/modules/whatsapp/message.model";

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

  return await Message.create({
    contactId,
    waMessageId,
    message,
    direction: "OUTBOUND",
    type: "text",
    rawPayload,
    status: "SENT",
  });
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

  const result = await Message.updateOne(
    { waMessageId },
    {
      $set: {
        status: status.toUpperCase(),
      },
    },
  );

  return result;
}

export async function getChatByWaId(waId: string) {
  await connectDB();

  const contact = await Contact.findOne({ waId });

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
          contactId: contact._id,
          direction: "INBOUND",
          status: "RECEIVED",
        }),
      ]);

      return {
        ...contact.toObject(),
        lastMessage: lastMessage?.message || "",
        lastMessageDirection: lastMessage?.direction,
        lastMessageCreatedAt: lastMessage?.createdAt,
        unreadCount,
      };
    }),
  );
}

export async function markMessagesAsRead(waId: string) {
  await connectDB();

  const contact = await Contact.findOne({
    waId,
  });

  if (!contact) return;

  const unreadMessages = await Message.find({
    contactId: contact._id,
    direction: "INBOUND",
    status: "RECEIVED",
  });

  for (const msg of unreadMessages) {
    try {
      if (
        process.env.WHATSAPP_ACCESS_TOKEN &&
        process.env.WHATSAPP_PHONE_NUMBER_ID
      ) {
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
        }
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

  return Contact.findByIdAndUpdate(
    contactId,
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

  return Contact.findByIdAndUpdate(
    contactId,
    {
      aiEnabled,
    },
    {
      new: true,
    },
  );
}
