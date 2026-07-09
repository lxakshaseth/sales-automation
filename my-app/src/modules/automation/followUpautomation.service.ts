import Lead from "@/modules/leads/leads.model";
import Campaign from "@/modules/campaign/campaign.model";
import Unsubscribed from "@/modules/Email/unsubscribed.model";
import { createAuditLog } from "@/modules/audit-log/auditLog.service";
import { emailQueue } from "@/queues/email.queue";
import { FOLLOW_UP_DELAYS_HOURS, MAX_FOLLOW_UP_STAGE } from "./followUpSequence.config";

const BATCH_SIZE = 200;

export const runFollowUpAutomationCycle = async () => {
  const ranAt = new Date();
  const candidates = await Lead.aggregate([
    {
      $match: {
        followUpStage: { $gte: 1, $lt: MAX_FOLLOW_UP_STAGE },
        lastEmailSentAt: { $ne: null },
      },
    },
    {
      $addFields: {
        requiredDelayHours: {
          $switch: {
            branches: [
              { case: { $eq: ["$followUpStage", 1] }, then: FOLLOW_UP_DELAYS_HOURS[1] },
              { case: { $eq: ["$followUpStage", 2] }, then: FOLLOW_UP_DELAYS_HOURS[2] },
              { case: { $eq: ["$followUpStage", 3] }, then: FOLLOW_UP_DELAYS_HOURS[3] },
            ],
            default: null,
          },
        },
      },
    },
    { $match: { requiredDelayHours: { $ne: null } } },
    {
      $addFields: {
        nextEligibleAt: {
          $add: ["$lastEmailSentAt", { $multiply: ["$requiredDelayHours", 60 * 60 * 1000] }],
        },
      },
    },
    { $match: { nextEligibleAt: { $lte: ranAt } } },
    {
      $lookup: {
        from: Unsubscribed.collection.name,
        localField: "email",
        foreignField: "email",
        as: "unsubscribeRecord",
      },
    },
    { $match: { unsubscribeRecord: { $size: 0 } } },
    { $project: { _id: 1, email: 1, firstName: 1, lastName: 1, company: 1, campaign: 1, followUpStage: 1 } },
    { $limit: BATCH_SIZE },
  ]);

  let queued = 0;
  let skipped = 0;

  for (const lead of candidates) {
    try {
      const nextStage = lead.followUpStage + 1;

      const campaign = lead.campaign ? await Campaign.findById(lead.campaign).populate("emailTemplates") : null;
      const template =
        campaign?.emailTemplates?.[nextStage - 1] ??
        campaign?.emailTemplates?.[campaign.emailTemplates.length - 1];

      if (!template) {
        skipped++;
        continue;
      }

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

      queued++;
    } catch (error) {
      skipped++;
      console.log(`[follow-up-automation] Failed for lead ${lead._id}:`, error);
    }
  }

  if (queued || skipped) {
    await createAuditLog(
      "Automation",
      "FollowUpCron",
      "Follow-up Sequence",
      `${queued} follow-up email(s) queued, ${skipped} skipped`,
    );
  }

  console.log(`[follow-up-automation] ranAt=${ranAt.toISOString()} queued=${queued} skipped=${skipped}`);

  return { ranAt, queued, skipped };
};