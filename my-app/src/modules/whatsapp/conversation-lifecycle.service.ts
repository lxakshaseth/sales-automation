import { randomUUID } from "crypto";

import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import Message from "@/modules/whatsapp/message.model";
import { sendEmail } from "@/modules/Email/email.controller";

import {
  saveOutboundMessage,
  sendWhatsAppTextMessage,
} from "./whatsapp.service";

const DEFAULT_REMINDER_AFTER_MS = 3 * 60 * 1000;
const DEFAULT_CLOSE_AFTER_MS = 5 * 60 * 1000;  // 5 minutes in milliseconds
const QUEUE_JOB_ATTEMPTS = 3;

type ConversationContact = {
  _id: unknown;
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

type LifecycleTimer = ReturnType<typeof setTimeout>;
type LifecycleTimerState = {
  runId: string;
  timers: LifecycleTimer[];
};

type LifecycleGlobalState = typeof globalThis & {
  __whatsappLifecycleTimers?: Map<string, LifecycleTimerState>;
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
  await connectDB();

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

  scheduleLocalLifecycle(contactId, runId);

  void scheduleQueuedLifecycle(contactId, runId).catch((error) => {
    console.error("[whatsapp:lifecycle] Failed to schedule queue jobs", {
      contactId,
      error,
    });
  });

  return runId;
}

async function scheduleQueuedLifecycle(contactId: string, runId: string) {
  const { whatsappLifecycleQueue } = await import(
    "@/queues/whatsapp-lifecycle.queue"
  );

  await Promise.all([
    whatsappLifecycleQueue.add(
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
        attempts: QUEUE_JOB_ATTEMPTS,
        backoff: {
          type: "fixed",
          delay: 30 * 1000,
        },
      },
    ),
    whatsappLifecycleQueue.add(
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
        attempts: QUEUE_JOB_ATTEMPTS,
        backoff: {
          type: "fixed",
          delay: 30 * 1000,
        },
      },
    ),
  ]);
}

function getLocalLifecycleTimers() {
  const state = globalThis as LifecycleGlobalState;

  if (!state.__whatsappLifecycleTimers) {
    state.__whatsappLifecycleTimers = new Map();
  }

  return state.__whatsappLifecycleTimers;
}

function scheduleLocalLifecycle(contactId: string, runId: string) {
  clearLocalLifecycleTimers(contactId);

  const reminderTimer = setTimeout(() => {
    runLocalLifecycleJob("send-reminder", contactId, runId);
  }, getReminderDelayMs());

  const closeTimer = setTimeout(() => {
    runLocalLifecycleJob("close-chat", contactId, runId);
  }, getCloseDelayMs());

  unrefTimer(reminderTimer);
  unrefTimer(closeTimer);

  getLocalLifecycleTimers().set(contactId, {
    runId,
    timers: [reminderTimer, closeTimer],
  });
}

function clearLocalLifecycleTimers(contactId: string) {
  const existing = getLocalLifecycleTimers().get(contactId);

  if (!existing) {
    return;
  }

  for (const timer of existing.timers) {
    clearTimeout(timer);
  }

  getLocalLifecycleTimers().delete(contactId);
}

function unrefTimer(timer: LifecycleTimer) {
  const maybeNodeTimer = timer as LifecycleTimer & { unref?: () => void };

  maybeNodeTimer.unref?.();
}

function runLocalLifecycleJob(
  jobName: "send-reminder" | "close-chat",
  contactId: string,
  runId: string,
) {
  void (async () => {
    try {
      if (jobName === "send-reminder") {
        await processReminderJob(contactId, runId);
        return;
      }

      await processCloseChatJob(contactId, runId);
    } catch (error) {
      console.error(`[whatsapp:lifecycle] Local ${jobName} failed`, {
        contactId,
        error,
      });
    } finally {
      if (jobName === "close-chat") {
        const activeTimers = getLocalLifecycleTimers().get(contactId);

        if (activeTimers?.runId === runId) {
          getLocalLifecycleTimers().delete(contactId);
        }
      }
    }
  })();
}

export async function processReminderJob(contactId: string, runId: string) {
  await connectDB();

  const reminderStartedAt = new Date();
  const contact = await Contact.findOneAndUpdate(
    {
      _id: contactId,
      lifecycleRunId: runId,
      conversationStatus: {
        $ne: "CLOSED",
      },
      reminderSentAt: null,
    },
    {
      $set: {
        reminderSentAt: reminderStartedAt,
      },
    },
    {
      new: true,
    },
  );

  if (!contact) {
    return;
  }

  const reminderMessage =
    process.env.WHATSAPP_REMINDER_MESSAGE ||
    "Just checking in. Please reply here whenever you are ready, and we will continue the conversation.";

  try {
    await sendLifecycleWhatsAppMessage({
      contact,
      message: reminderMessage,
      failureLabel: "WhatsApp reminder",
    });
  } catch (error) {
    await Contact.updateOne(
      {
        _id: contactId,
        lifecycleRunId: runId,
        reminderSentAt: reminderStartedAt,
      },
      {
        $set: {
          reminderSentAt: null,
        },
      },
    );

    throw error;
  }
}

export async function processCloseChatJob(contactId: string, runId: string) {
  await connectDB();

  const closeStartedAt = new Date();
  const contact = await Contact.findOneAndUpdate(
    {
      _id: contactId,
      lifecycleRunId: runId,
      conversationStatus: {
        $ne: "CLOSED",
      },
      closedAt: null,
    },
    {
      $set: {
        conversationStatus: "CLOSED",
        closedAt: closeStartedAt,
      },
    },
    {
      new: true,
    },
  );

  if (!contact) {
    return;
  }

  const closeMessage =
    process.env.WHATSAPP_CLOSE_MESSAGE ||
    "I will close this conversation for now. You can message anytime if you need more help.";

  try {
    await sendLifecycleWhatsAppMessage({
      contact,
      message: closeMessage,
      failureLabel: "WhatsApp close message",
    });
  } catch (error) {
    await Contact.updateOne(
      {
        _id: contactId,
        lifecycleRunId: runId,
        closedAt: closeStartedAt,
      },
      {
        $set: {
          conversationStatus: "OPEN",
          closedAt: null,
        },
      },
    );

    throw error;
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

    await Contact.updateOne(
      {
        _id: contact._id,
        lifecycleRunId: runId,
      },
      {
        $set: {
          summarySentAt: new Date(),
        },
      },
    );
  }
}

async function sendLifecycleWhatsAppMessage({
  contact,
  message,
  failureLabel,
}: {
  contact: ConversationContact;
  message: string;
  failureLabel: string;
}) {
  const sendResult = await sendWhatsAppTextMessage({
    to: contact.waId,
    message,
  });

  if (!sendResult.ok) {
    throw new Error(
      `${failureLabel} failed with status ${sendResult.status}: ${JSON.stringify(
        sendResult.data,
      )}`,
    );
  }

  await saveOutboundMessage({
    contactId: String(contact._id),
    waMessageId: sendResult.data?.messages?.[0]?.id,
    message,
    rawPayload: sendResult.data,
  });
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
