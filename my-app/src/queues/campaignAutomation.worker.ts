import { Worker } from "bullmq";

import { redisConnection } from "./redis";
import connectDB from "@/lib/db";
import { runCampaignAutomationCycle } from "@/modules/automation/campaignAutomation.service";

export const campaignAutomationWorker = new Worker(
  "campaignAutomationQueue",

  async (job) => {
    try {
      console.log("[campaign-automation] Cron tick, job:", job.id);

      await connectDB();

      await runCampaignAutomationCycle();
    } catch (error) {
      console.log("[campaign-automation] WORKER ERROR:", error);
    }
  },

  {
    connection: redisConnection,
  },
);

console.log("Campaign Automation Worker Running");
