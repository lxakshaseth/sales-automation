import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import Message from "@/modules/whatsapp/message.model";

export async function upsertContact({
  waId,
  name,
  phone,
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
  rawPayload: any;
}) {
  await connectDB();

  return await Message.create({
    contactId,
    waMessageId,
    message,
    direction: "INBOUND",
    type: "text",
    rawPayload,
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
  rawPayload: any;
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

  return Contact.find()
    .sort({
      lastMessageAt: -1,
    });
}