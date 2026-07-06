import assert from "node:assert/strict";
import test from "node:test";

import { sendConversationSummaryToOwner } from "./conversation-lifecycle.service";

test("generates a summary PDF and sends it to the owner", async () => {
  const closedAt = new Date("2026-07-06T10:30:00.000Z");
  const sentEmails: unknown[] = [];
  let pdfGenerated = false;

  const sent = await sendConversationSummaryToOwner({
    ownerEmail: "owner@example.com",
    contact: {
      _id: "contact-1",
      waId: "919999999999",
      name: "Client One",
      phone: "919999999999",
      conversationStatus: "CLOSED",
      closedAt,
    },
    messages: [
      {
        direction: "INBOUND",
        message: "I need pricing details.",
        createdAt: new Date("2026-07-06T10:00:00.000Z"),
      },
      {
        direction: "OUTBOUND",
        message: "Sure, here are the available plans.",
        createdAt: new Date("2026-07-06T10:01:00.000Z"),
      },
      {
        direction: "INBOUND",
        message: "Thanks, bye.",
        createdAt: closedAt,
      },
    ],
    buildSummaryPdf: ({ contact, messages }) => {
      pdfGenerated = true;

      assert.equal(contact.waId, "919999999999");
      assert.equal(messages.length, 3);

      return Buffer.from("summary-pdf");
    },
    sendOwnerEmail: async (email) => {
      sentEmails.push(email);
    },
  });

  assert.equal(sent, true);
  assert.equal(pdfGenerated, true);
  assert.equal(sentEmails.length, 1);

  const [email] = sentEmails as {
    to: string;
    subject: string;
    body: string;
    attachments: { filename: string; content: Buffer; contentType: string }[];
  }[];

  assert.equal(email.to, "owner@example.com");
  assert.match(email.subject, /Conversation Summary - Client One/);
  assert.match(email.body, /Conversation Summary/);
  assert.match(email.body, /I need pricing details\./);
  assert.equal(email.attachments.length, 1);
  assert.equal(email.attachments[0]?.contentType, "application/pdf");
  assert.equal(email.attachments[0]?.content.toString(), "summary-pdf");
});

test("skips owner summary notification when no owner email is configured", async () => {
  let sendAttempted = false;

  const sent = await sendConversationSummaryToOwner({
    contact: {
      _id: "contact-1",
      waId: "919999999999",
      closedAt: new Date("2026-07-06T10:30:00.000Z"),
    },
    messages: [],
    sendOwnerEmail: async () => {
      sendAttempted = true;
    },
  });

  assert.equal(sent, false);
  assert.equal(sendAttempted, false);
});
