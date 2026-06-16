import {
  upsertContact,
  saveInboundMessage,
  updateMessageStatus,
  getContacts,
  getChatByWaId,
  markMessagesAsRead,
  updateContactName,
} from "./whatsapp.service";

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
