import { randomUUID } from "crypto";

import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import Message from "@/modules/whatsapp/message.model";
import { sendEmail } from "@/modules/Email/email.controller";
import { buildConversationSummaryPdf } from "@/modules/whatsapp/conversation-summary-pdf";

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
  closedAt?: Date | string;
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

  const ownerEmail = process.env.OWNER_EMAIL;

  if (ownerEmail) {
    const summary = buildConversationSummary({
      contact,
      messages,
    });
    const summaryPdf = buildConversationSummaryPdf({
      contact,
      messages,
    });
    const contactLabel = getContactLabel(contact);
    const closedDate = formatSummaryDate(contact.closedAt || closeStartedAt);

    await sendEmail({
      to: ownerEmail,
      subject: `Conversation Summary - ${contactLabel} (${closedDate})`,
      body: summary,
      attachments: [
        {
          filename: getSummaryPdfFileName(contactLabel, closedDate),
          content: summaryPdf,
          contentType: "application/pdf",
        },
      ],
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
  const closedAt = contact.closedAt ? new Date(contact.closedAt) : new Date();
  const firstMessageAt = messages.length
    ? new Date(messages[0].createdAt)
    : closedAt;
  const customerMessages = messages.filter(
    (message) => message.direction === "INBOUND",
  ).length;
  const businessMessages = messages.filter(
    (message) => message.direction === "OUTBOUND",
  ).length;
  const transcript = messages
    .slice(-20)
    .map((message) => {
      const speaker = message.direction === "INBOUND" ? "Client" : "Business";
      const time = formatSummaryTime(message.createdAt);
      const bubbleColor =
        message.direction === "INBOUND" ? "#eff6ff" : "#ecfdf5";
      const speakerColor =
        message.direction === "INBOUND" ? "#2563eb" : "#059669";

      return `
        <tr>
          <td style="width:86px;color:#64748b;font-size:12px;vertical-align:top;padding:9px 8px 9px 0;">${time}</td>
          <td style="width:82px;color:${speakerColor};font-size:12px;font-weight:700;vertical-align:top;padding:9px 8px;">${speaker}</td>
          <td style="padding:6px 0;">
            <div style="background:${bubbleColor};border:1px solid #dbeafe;border-radius:8px;padding:10px 12px;color:#0f172a;font-size:13px;line-height:1.45;">
              ${escapeHtml(message.message || "")}
            </div>
          </td>
        </tr>
      `;
    })
    .join("");

  return `
    <div style="margin:0;padding:24px;background:#f7f8fc;font-family:Inter,Arial,sans-serif;color:#0f172a;">
      <div style="max-width:860px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:16px;overflow:hidden;">
        <div style="background:#090a2f;padding:28px 34px;color:#ffffff;">
          <div style="font-size:28px;font-weight:800;letter-spacing:-0.2px;">Conversation Summary</div>
          <div style="margin-top:8px;color:#dbeafe;font-size:15px;">Detailed chat transcript with customer</div>
          <div style="margin-top:18px;display:inline-block;background:#15145a;border-radius:12px;padding:10px 14px;font-size:13px;">
            <strong>Closed</strong> - ${formatSummaryDateTime(closedAt)}
          </div>
        </div>

        <div style="padding:26px 34px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
            <tr>
              <td style="width:50%;vertical-align:top;padding-right:18px;">
                <div style="font-size:13px;font-weight:800;color:#1e1b8f;margin-bottom:14px;">CUSTOMER DETAILS</div>
                ${detailHtml("Contact Name", getContactLabel(contact))}
                ${detailHtml("Phone Number", contact.phone || contact.waId)}
                ${detailHtml("Status", "Closed")}
              </td>
              <td style="vertical-align:top;border-left:1px solid #e5e7eb;padding-left:24px;">
                <div style="font-size:13px;font-weight:800;color:#1e1b8f;margin-bottom:14px;">CONVERSATION OVERVIEW</div>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:separate;border-spacing:8px 0;">
                  <tr>
                    ${statHtml(String(customerMessages), "Customer Messages", "#eff6ff")}
                    ${statHtml(String(businessMessages), "Business Messages", "#ecfdf5")}
                    ${statHtml(String(messages.length), "Total Messages", "#f3e8ff")}
                    ${statHtml(formatSummaryDuration(closedAt.getTime() - firstMessageAt.getTime()), "Duration", "#fff7ed")}
                  </tr>
                </table>
              </td>
            </tr>
          </table>

          <div style="margin-top:28px;border-top:1px solid #e5e7eb;padding-top:20px;">
            <div style="font-size:13px;font-weight:800;color:#1e1b8f;margin-bottom:12px;">CHAT TRANSCRIPT</div>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
              ${transcript || `<tr><td style="color:#64748b;font-size:13px;">No messages found.</td></tr>`}
            </table>
          </div>

          <div style="margin-top:24px;background:#f5f3ff;border:1px solid #ddd6fe;border-radius:12px;padding:16px 18px;">
            <div style="font-weight:800;color:#1e1b8f;">PDF summary attached</div>
            <div style="margin-top:6px;color:#475569;font-size:13px;line-height:1.45;">The attached PDF contains the polished summary layout, customer details, overview metrics, transcript, topics, sentiment, and follow-up prompt.</div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function detailHtml(label: string, value: string) {
  return `
    <div style="margin-bottom:14px;">
      <div style="color:#64748b;font-size:12px;">${escapeHtml(label)}</div>
      <div style="font-size:14px;font-weight:700;color:#0f172a;margin-top:3px;">${escapeHtml(value || "--")}</div>
    </div>
  `;
}

function statHtml(value: string, label: string, background: string) {
  return `
    <td style="background:${background};border:1px solid #e5e7eb;border-radius:12px;text-align:center;padding:14px 8px;">
      <div style="font-size:22px;font-weight:800;color:#0f172a;">${escapeHtml(value)}</div>
      <div style="font-size:11px;color:#334155;line-height:1.25;">${escapeHtml(label)}</div>
    </td>
  `;
}

function formatSummaryDate(value: Date | string) {
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata",
  });
}

function formatSummaryDateTime(value: Date | string) {
  return uppercaseMeridiem(
    new Date(value).toLocaleString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata",
    }),
  );
}

function formatSummaryTime(value: Date | string) {
  return uppercaseMeridiem(
    new Date(value).toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
      timeZone: "Asia/Kolkata",
    }),
  );
}

function formatSummaryDuration(durationMs: number) {
  const totalMinutes = Math.max(1, Math.round(durationMs / 60000));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours > 0) {
    return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  }

  return `${minutes}m`;
}

function getSummaryPdfFileName(contactLabel: string, closedDate: string) {
  return `conversation-summary-${slugifyFileName(contactLabel)}-${slugifyFileName(
    closedDate,
  )}.pdf`;
}

function slugifyFileName(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
}

function uppercaseMeridiem(value: string) {
  return value.replace(/\b(am|pm)\b/gi, (period) => period.toUpperCase());
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
