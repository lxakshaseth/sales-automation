import {
  upsertContact,
  saveInboundMessage,
  updateMessageStatus,
  getContacts,
  getChatByWaId,
  markMessagesAsRead,
  saveOutboundMessage,
  sendWhatsAppTextMessage,
  updateContactAiEnabled,
  updateContactName,
} from "./whatsapp.service";
import { generateSalesReply } from "@/modules/whatsapp/ai-reply.service";
import { startConversationLifecycle } from "@/modules/whatsapp/conversation-lifecycle.service";

export async function handleIncomingMessage(payload: any) {
  console.log("handleIncomingMessage called");
  const value = payload.entry?.[0]?.changes?.[0]?.value;

  const contacts = value?.contacts || [];
  const messages = value?.messages || [];

  if (!messages.length) return;

  const contactData = contacts[0];
  const msg = messages[0];

  const contact = await upsertContact({
    waId: contactData?.wa_id,
    name: contactData?.profile?.name,
    phone: contactData?.wa_id,
  });

  await saveInboundMessage({
    contactId: contact._id,
    waMessageId: msg.id,
    message: msg?.text?.body,
    rawPayload: payload,
  });

  await startConversationLifecycle(contact._id.toString());

  if (!contact.aiEnabled || !msg?.text?.body?.trim()) {   // If AI is not enabled for the contact or the message body is empty, do not generate a reply
    return;
  }

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

export async function handleStatusUpdate(payload: any) {
  const value = payload.entry?.[0]?.changes?.[0]?.value;

  const statuses = value?.statuses || [];

  if (!statuses.length) return;

  const status = statuses[0];

  await updateMessageStatus({
    waMessageId: status.id,
    status: status.status,
  });
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
