import Lead from "@/modules/leads/leads.model";
import Campaign from "@/modules/campaign/campaign.model";
import Unsubscribed from "@/modules/Email/unsubscribed.model";
import { createAuditLog } from "@/modules/audit-log/auditLog.service";

import { startCampaignFlow } from "./automation.service";

const ELIGIBILITY_WINDOW_MS = 24 * 60 * 60 * 1000; // 24 hours
const BATCH_SIZE = 200; // cap per cron tick so one run can't overload the email queue

export type CampaignAutomationResult = {
  ranAt: Date;
  campaignId: string | null;
  campaignName: string | null;
  eligibleLeadCount: number;
  assignedLeadCount: number;
  skippedLeadCount: number;
};

export const runCampaignAutomationCycle =
  async (): Promise<CampaignAutomationResult> => {
    const ranAt = new Date();

    const campaign = await Campaign.findOne({ status: "active" }).sort({
      updatedAt: -1,
    });

    if (!campaign) {
      console.log(
        "[campaign-automation] No active campaign found. Skipping cycle.",
      );

      return {
        ranAt,
        campaignId: null,
        campaignName: null,
        eligibleLeadCount: 0,
        assignedLeadCount: 0,
        skippedLeadCount: 0,
      };
    }

    const cutoff = new Date(ranAt.getTime() - ELIGIBILITY_WINDOW_MS);

    const eligibleLeads = await Lead.aggregate([
      {
        $match: {
          $or: [
            { lastEmailSentAt: { $exists: false } },
            { lastEmailSentAt: null },
            { lastEmailSentAt: { $lte: cutoff } },
          ],
        },
      },
      {
        $lookup: {
          from: Unsubscribed.collection.name,
          localField: "email",
          foreignField: "email",
          as: "unsubscribeRecord",
        },
      },
      {
        $match: { unsubscribeRecord: { $size: 0 } },
      },
      {
        $project: { _id: 1, email: 1 },
      },
      { $limit: BATCH_SIZE },
    ]);

    if (eligibleLeads.length === 0) {
      console.log(
        `[campaign-automation] Active campaign "${campaign.name}" has no eligible leads this cycle.`,
      );

      return {
        ranAt,
        campaignId: campaign._id.toString(),
        campaignName: campaign.name,
        eligibleLeadCount: 0,
        assignedLeadCount: 0,
        skippedLeadCount: 0,
      };
    }

    const leadIds = eligibleLeads.map((lead) => lead._id);

    await Lead.updateMany(
      { _id: { $in: leadIds } },
      { $set: { campaign: campaign._id } },
    );

    let assignedLeadCount = 0;
    let skippedLeadCount = 0;

    for (const lead of eligibleLeads) {
      try {
        await startCampaignFlow(lead._id.toString());
        assignedLeadCount += 1;
      } catch (error) {
        skippedLeadCount += 1;
        console.log(
          `[campaign-automation] Failed to start campaign flow for lead ${lead._id}:`,
          error,
        );
      }
    }

    await createAuditLog(
      "Automation",
      "Cron",
      campaign.name,
      `${assignedLeadCount} lead(s) assigned and queued for email` +
        (skippedLeadCount ? `, ${skippedLeadCount} skipped due to errors` : ""),
    );

    console.log(
      `[campaign-automation] Campaign "${campaign.name}": ${assignedLeadCount} assigned, ${skippedLeadCount} skipped.`,
    );

    return {
      ranAt,
      campaignId: campaign._id.toString(),
      campaignName: campaign.name,
      eligibleLeadCount: eligibleLeads.length,
      assignedLeadCount,
      skippedLeadCount,
    };
  };
