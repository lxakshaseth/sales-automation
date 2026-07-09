import Lead from "./leads.model";
import Campaign from "@/modules/campaign/campaign.model";
import Unsubscribed from "@/modules/Email/unsubscribed.model";
import { emailQueue } from "@/queues/email.queue";
import { FOLLOW_UP_DELAYS_HOURS, MAX_FOLLOW_UP_STAGE } from "@/modules/automation/followUpSequence.config";

export const sendManualFollowUpEmail = async (leadId: string, force = false) => {
  const lead = await Lead.findById(leadId).populate({
    path: "campaign",
    populate: { path: "emailTemplates" },
  });
  if (!lead) throw new Error("Lead not found");

  const unsubscribed = await Unsubscribed.findOne({ email: lead.email });
  if (unsubscribed) throw new Error("Contact has unsubscribed");

  if (lead.followUpStage >= MAX_FOLLOW_UP_STAGE) {
    throw new Error("Follow-up sequence already completed for this contact — no more emails will be sent");
  }

  const nextStage = lead.followUpStage + 1;

  // Enforce the wait window unless explicitly overridden
  if (!force && lead.followUpStage >= 1) {
    const requiredHours = FOLLOW_UP_DELAYS_HOURS[lead.followUpStage];
    const dueAt = new Date(lead.lastEmailSentAt.getTime() + requiredHours * 60 * 60 * 1000);
    if (new Date() < dueAt) {
      throw new Error(`Not due yet. Next email is eligible at ${dueAt.toISOString()} (pass force=true to send now anyway)`);
    }
  }

  const campaign: any = lead.campaign;
  const template =
    campaign?.emailTemplates?.[nextStage - 1] ??
    campaign?.emailTemplates?.[campaign?.emailTemplates?.length - 1];

  if (!template) throw new Error("No email template available for this stage");

  await emailQueue.add("send-email", {
    to: lead.email,
    leadId: lead._id.toString(),
    subject: template.subject,
    body: template.body,
    followUpStage: nextStage,
    variables: {
      first_name: lead.firstName,
      last_name: lead.lastName || "",
      company: lead.company || "",
      email: lead.email,
    },
  });

  return { leadId, queuedStage: nextStage };
};