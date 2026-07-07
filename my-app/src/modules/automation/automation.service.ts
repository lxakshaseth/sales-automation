import Lead from "@/modules/leads/leads.model";

import { emailQueue } from "@/queues/email.queue";

export const startCampaignFlow = async (leadId: string) => {
  // 1. Fetch lead with campaign
  const lead = await Lead.findById(leadId).populate({
    path: "campaign",

    populate: {
      path: "emailTemplates",
    },
  });

  if (!lead) {
    throw new Error("Lead not found");
  }

  const campaign: any = lead.campaign;

  if (!campaign) {
    throw new Error("Campaign not found");
  }

  // 2. Guard: never run automation for a campaign that isn't active
  if (campaign.status !== "active") {
    console.log(
      `Skipping automation: campaign "${campaign.name}" is "${campaign.status}", not active`,
    );
    return;
  }

  // 3. Get first enabled funnel step
  const firstStep = campaign.funnel.find((step: any) => step.enabled);

  if (!firstStep) {
    throw new Error("No enabled funnel step found");
  }

  // 4. Handle email step only
  if (firstStep.step === "email") {
    // 5. Find matching template
    const template = campaign.emailTemplates?.[0];

    if (!template) {
      throw new Error("No email template attached to this campaign");
    }

    // 6. Queue email job
    await emailQueue.add("send-email", {
      to: lead.email,

      leadId: lead._id.toString(),

      subject: template.subject,

      body: template.body,

      variables: {
        first_name: lead.firstName,
        last_name: lead.lastName || "",
        company: lead.company || "",
        email: lead.email,
      },
    });

    console.log("Email job added to queue successfully");
  }
};