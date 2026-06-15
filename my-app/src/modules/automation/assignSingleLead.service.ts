import Lead from "@/modules/leads/leads.model";
import Campaign from "@/modules/campaign/campaign.model";

import { startCampaignFlow } from "./automation.service";

export const assignSingleLead = async (
  leadId: string,
  campaignId: string,
) => {
  const lead = await Lead.findById(leadId);

  if (!lead) {
    throw new Error("Lead not found");
  }

  if (lead.campaign) {
  throw new Error(
    "Lead is already assigned to a campaign",
  );
}

  const campaign = await Campaign.findById(
    campaignId,
  );

  if (!campaign) {
    throw new Error("Campaign not found");
  }

  lead.campaign = campaign._id;

  await lead.save();

  await startCampaignFlow(
    lead._id.toString(),
  );

  return lead;
};