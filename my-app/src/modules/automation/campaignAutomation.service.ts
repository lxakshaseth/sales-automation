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

/**
 * 1. Finds the single active campaign.
 * 2. Fetches leads that are not unsubscribed and whose last email
 *    (if any) went out 24h+ ago.
 * 3. Assigns them to the active campaign and kicks off the email step.
 *
 * lastEmailSentAt itself is only updated by the email worker once a
 * send actually succeeds (see queues/email.worker.ts).
 */
export const runCampaignAutomationCycle =
  async (): Promise<CampaignAutomationResult> => {
    const ranAt = new Date();

    // 1. Find the active campaign. Only one is expected to be active at a
    // time; if more than one is ever marked active (e.g. due to manual DB
    // edits), the most recently updated one wins and the rest are ignored
    // this cycle.
    const campaign = await Campaign.findOne({ status: "active" }).sort({
      updatedAt: -1,
    });

    if (!campaign) {
      console.log("[campaign-automation] No active campaign found. Skipping cycle.");

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

    // 2. Fetch eligible leads: not unsubscribed, and either never emailed
    // or last emailed 24h+ ago. Use the live Unsubscribed collection name
    // rather than hardcoding it, in case pluralization ever changes.
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

    // 3. Assign eligible leads to the active campaign.
    await Lead.updateMany(
      { _id: { $in: leadIds } },
      { $set: { campaign: campaign._id } },
    );

    let assignedLeadCount = 0;
    let skippedLeadCount = 0;

    // Fire the campaign's first funnel step (email) for each lead. Run
    // sequentially to avoid hammering the queue/DB in one burst; the queue
    // itself is durable so a mid-batch crash just resumes leads on the
    // next cron tick since lastEmailSentAt is only set on real delivery.
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