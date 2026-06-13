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

  // 2. Get first enabled funnel step
  const firstStep = campaign.funnel.find((step: any) => step.enabled);

  if (!firstStep) {
    throw new Error("No enabled funnel step found");
  }

  // 3. Handle email step only
  if (firstStep.step === "email") {
    // 4. Find matching template
    const template = campaign.emailTemplates.find(
      (template: any) => template.name === firstStep.action,
    );

    if (!template) {
      throw new Error(`Template not found for action: ${firstStep.action}`);
    }

    // 5. Queue email job
    await emailQueue.add("send-email", {
      to: lead.email,

      subject: template.subject,

      body: template.body,

      variables: {
        firstName: lead.firstName,
        lastName: lead.lastName || "",
        company: lead.company || "",
        email: lead.email,
      },
    });

    console.log("Email job added to queue successfully");
  }
};
