import { randomUUID } from "crypto";

import Contact from "@/modules/whatsapp/contact.model";
import Message from "@/modules/whatsapp/message.model";
import { sendEmail } from "@/modules/Email/email.controller";

import {
  saveOutboundMessage,
  sendWhatsAppTextMessage,
} from "./whatsapp.service";

const DEFAULT_REMINDER_AFTER_MS = 3 * 60 * 1000;
const DEFAULT_CLOSE_AFTER_MS = 5 * 60 * 1000;  // 5 minutes in milliseconds

type ConversationContact = {
  customName?: string;
  name?: string;
  phone?: string;
  waId: string;
  lifecycleRunId?: string;
  conversationStatus?: string;
};

type ConversationMessage = {
  direction: "INBOUND" | "OUTBOUND";
  message?: string;
  createdAt: Date | string;
};

function getDelayMs(envValue: string | undefined, fallback: number) {
  const value = Number(envValue);

  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function getReminderDelayMs() {
  return getDelayMs(process.env.WHATSAPP_REMINDER_AFTER_MS, DEFAULT_REMINDER_AFTER_MS);
}

function getCloseDelayMs() {
  return getDelayMs(process.env.WHATSAPP_CLOSE_AFTER_MS, DEFAULT_CLOSE_AFTER_MS);
}

export async function startConversationLifecycle(contactId: string) {
  const runId = randomUUID();
  const now = new Date();

  await Contact.findByIdAndUpdate(contactId, {
    lifecycleRunId: runId,
    lastInboundAt: now,
    conversationStatus: "OPEN",
    reminderSentAt: null,
    closedAt: null,
    summarySentAt: null,
  });

  try {
    const { whatsappLifecycleQueue } = await import(
      "@/queues/whatsapp-lifecycle.queue"
    );

    await whatsappLifecycleQueue.add(
      "send-reminder",
      {
        contactId,
        runId,
      },
      {
        delay: getReminderDelayMs(),
        jobId: `whatsapp-reminder:${contactId}:${runId}`,
        removeOnComplete: true,
        removeOnFail: 50,
      },
    );

    await whatsappLifecycleQueue.add(
      "close-chat",
      {
        contactId,
        runId,
      },
      {
        delay: getCloseDelayMs(),
        jobId: `whatsapp-close:${contactId}:${runId}`,
        removeOnComplete: true,
        removeOnFail: 50,
      },
    );
  } catch (error) {
    console.error("[whatsapp:lifecycle] Failed to schedule jobs", {
      contactId,
      error,
    });
  }

  return runId;
}

export async function processReminderJob(contactId: string, runId: string) {
  const contact = await Contact.findById(contactId);

  if (!contact || !isCurrentOpenRun(contact, runId) || contact.reminderSentAt) {
    return;
  }

  const reminderMessage =
    process.env.WHATSAPP_REMINDER_MESSAGE ||
    "Just checking in. Please reply here whenever you are ready, and we will continue the conversation.";

  const sendResult = await sendWhatsAppTextMessage({
    to: contact.waId,
    message: reminderMessage,
  });

  if (!sendResult.ok) {
    throw new Error(
      `WhatsApp reminder failed with status ${sendResult.status}: ${JSON.stringify(
        sendResult.data,
      )}`,
    );
  }

  await saveOutboundMessage({
    contactId: contact._id,
    waMessageId: sendResult.data?.messages?.[0]?.id,
    message: reminderMessage,
    rawPayload: sendResult.data,
  });

  contact.reminderSentAt = new Date();
  contact.lastMessageAt = new Date();
  await contact.save();
}

export async function processCloseChatJob(contactId: string, runId: string) {
  const contact = await Contact.findById(contactId);

  if (!contact || !isCurrentOpenRun(contact, runId) || contact.closedAt) {
    return;
  }

  const messages = await Message.find({
    contactId: contact._id,
  })
    .sort({ createdAt: 1 })
    .lean();

  const summary = buildConversationSummary({
    contact,
    messages,
  });

  const ownerEmail = process.env.OWNER_EMAIL;

  if (ownerEmail) {
    await sendEmail({
      to: ownerEmail,
      subject: `WhatsApp chat summary: ${getContactLabel(contact)}`,
      body: summary,
    });

    contact.summarySentAt = new Date();
  }

  contact.conversationStatus = "CLOSED";
  contact.closedAt = new Date();
  await contact.save();
}

function isCurrentOpenRun(contact: ConversationContact, runId: string) {
  return (
    contact.lifecycleRunId === runId &&
    contact.conversationStatus !== "CLOSED"
  );
}

function getContactLabel(contact: ConversationContact) {
  return contact.customName || contact.name || contact.phone || contact.waId;
}

function buildConversationSummary({
  contact,
  messages,
}: {
  contact: ConversationContact;
  messages: ConversationMessage[];
}) {
  const transcript = messages
    .slice(-20)
    .map((message) => {
      const speaker = message.direction === "INBOUND" ? "Client" : "Business";
      const time = new Date(message.createdAt).toLocaleString("en-IN");

      return `<li><strong>${speaker}</strong> <span style="color:#64748b">(${time})</span>: ${escapeHtml(
        message.message || "",
      )}</li>`;
    })
    .join("");

  return `
    <h2>WhatsApp chat closed</h2>
    <p><strong>Contact:</strong> ${escapeHtml(getContactLabel(contact))}</p>
    <p><strong>Phone:</strong> ${escapeHtml(contact.phone || contact.waId)}</p>
    <p><strong>Total messages:</strong> ${messages.length}</p>
    <h3>Recent conversation</h3>
    <ol>${transcript || "<li>No messages found.</li>"}</ol>
  `;
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
