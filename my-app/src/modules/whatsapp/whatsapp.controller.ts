import {
  upsertContact,
  saveInboundMessage,
  updateMessageStatus,
  getContacts,
  getChatByWaId,
  messageExistsByWaMessageId,
  markMessagesAsRead,
  saveOutboundMessage,
  sendWhatsAppTextMessage,
  updateContactAiEnabled,
  updateContactName,
} from "./whatsapp.service";
import { generateSalesReply } from "@/modules/whatsapp/ai-reply.service";
import { startConversationLifecycle } from "@/modules/whatsapp/conversation-lifecycle.service";

type WhatsAppWebhookMessage = {
  id?: string;
  from?: string;
  type?: string;
  text?: {
    body?: string;
  };
};

type WhatsAppWebhookContact = {
  wa_id?: string;
  profile?: {
    name?: string;
  };
};

type WhatsAppWebhookStatus = {
  id?: string;
  status?: string;
};

type WhatsAppWebhookPayload = {
  entry?: {
    changes?: {
      value?: {
        contacts?: WhatsAppWebhookContact[];
        messages?: WhatsAppWebhookMessage[];
        statuses?: WhatsAppWebhookStatus[];
      };
    }[];
  }[];
};

function getWebhookValues(payload: WhatsAppWebhookPayload) {
  return (
    payload.entry?.flatMap((entry) =>
      entry.changes?.map((change) => change.value) || [],
    ) || []
  );
}

function isActualCustomerMessage(
  msg: WhatsAppWebhookMessage | undefined,
): msg is WhatsAppWebhookMessage & { id: string; from: string } {
  return Boolean(msg?.id && msg?.from && msg?.type !== "system");
}

function getIncomingMessageText(msg: WhatsAppWebhookMessage) {
  return typeof msg?.text?.body === "string" ? msg.text.body : "";
}

export async function handleIncomingMessage(payload: WhatsAppWebhookPayload) {
  const value = getWebhookValues(payload).find(
    (webhookValue) => Boolean(webhookValue?.messages?.length),
  );

  const contacts = value?.contacts || [];
  const messages = value?.messages || [];

  if (!messages.length) return;

  console.log("handleIncomingMessage called");

  const contactData = contacts[0];
  const msg = messages[0];
  const waId = contactData?.wa_id || msg?.from;

  if (!isActualCustomerMessage(msg) || !waId) {
    return;
  }

  if (await messageExistsByWaMessageId(msg.id)) {
    return;
  }

  const contact = await upsertContact({
    waId,
    name: contactData?.profile?.name,
    phone: waId,
  });

  await saveInboundMessage({
    contactId: contact._id,
    waMessageId: msg.id,
    message: getIncomingMessageText(msg),
    rawPayload: payload,
  });

  await startConversationLifecycle(contact._id.toString());

  if (!contact.aiEnabled || !msg?.text?.body?.trim()) {   // If AI is not enabled for the contact or the message body is empty, do not generate a reply
    return;
  }

  await markMessagesAsRead(contact.waId);

  const chat = await getChatByWaId(contact.waId);
  const reply = await generateSalesReply({
    message: msg.text.body,
    waId: contact.waId,
    history: chat?.messages || [],
  });

  const sendResult = await sendWhatsAppTextMessage({
    to: contact.waId,
    message: reply,
  });

  if (!sendResult.ok) {
    console.error("[whatsapp:ai] Failed to send AI reply", {
      waId: contact.waId,
      status: sendResult.status,
      data: sendResult.data,
    });

    return;
  }

  await saveOutboundMessage({
    contactId: contact._id,
    waMessageId: sendResult.data?.messages?.[0]?.id,
    message: reply,
    rawPayload: sendResult.data,
  });
}

export async function handleStatusUpdate(payload: WhatsAppWebhookPayload) {
  const statuses = getWebhookValues(payload).flatMap(
    (value) => value?.statuses || [],
  );

  if (!statuses.length) return;

  for (const status of statuses) {
    if (!status?.id || !status?.status) {
      continue;
    }

    await updateMessageStatus({
      waMessageId: status.id,
      status: status.status,
    });
  }
}

export async function getContactsController() {
  return await getContacts();
}

export async function getChatController(waId: string) {
  return await getChatByWaId(waId);
}

export async function updateContactNameController(
  contactId: string,
  customName: string,
) {
  return updateContactName(contactId, customName);
}

export async function updateContactAiEnabledController(
  contactId: string,
  aiEnabled: boolean,
) {
  return updateContactAiEnabled(contactId, aiEnabled);
}
