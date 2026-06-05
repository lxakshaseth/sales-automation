import Lead from "@/modules/leads/leads.model";
import Campaign from "@/modules/campaign/campaign.model";

import { startCampaignFlow } from "./automation.service";

export const assignMultipleLeadsToCampaign = async (
  leadIds: string[],
  campaignId: string,
) => {
  const campaign = await Campaign.findById(campaignId);

  if (!campaign) {
    throw new Error("Campaign not found");
  }

  const leads = await Lead.find({
    _id: {
      $in: leadIds,
    },
  });

  const assignedLeads = [];
  const skippedLeads = [];

  for (const lead of leads) {
    if (lead.campaign) {
      skippedLeads.push(lead);
      continue;
    }

    lead.campaign = campaign._id;

    await lead.save();

    await startCampaignFlow(lead._id.toString());

    assignedLeads.push(lead);
  }

  return {
    assignedLeads,
    skippedLeads,
  };
};
