import { Queue } from "bullmq";

import { redisConnection } from "./redis";

export const CAMPAIGN_AUTOMATION_JOB_NAME = "run-campaign-automation";
export const CAMPAIGN_AUTOMATION_REPEAT_JOB_ID = "campaign-automation-cron";
const FIVE_MINUTES_MS = 5 * 60 * 1000;

export const campaignAutomationQueue = new Queue(
  "campaignAutomationQueue",
  {
    connection: redisConnection,
  },
);

export const scheduleCampaignAutomationCron = async () => {
  await campaignAutomationQueue.add(
    CAMPAIGN_AUTOMATION_JOB_NAME,
    {},
    {
      repeat: {
        every: FIVE_MINUTES_MS,
      },
      jobId: CAMPAIGN_AUTOMATION_REPEAT_JOB_ID,
      removeOnComplete: true,
      removeOnFail: 50,
    },
  );

  console.log("Campaign Automation Cron Scheduled (every 5 minutes)");
};

console.log("Campaign Automation Queue Ready");