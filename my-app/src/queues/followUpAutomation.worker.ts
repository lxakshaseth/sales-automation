import { Worker } from "bullmq";
import { redisConnection } from "./redis";
import connectDB from "@/lib/db";
import { runFollowUpAutomationCycle } from "@/modules/automation/followUpautomation.service";

export const followUpAutomationWorker = new Worker(
  "followUpAutomationQueue",
  async (job) => {
    try {
      await connectDB();
      await runFollowUpAutomationCycle();
    } catch (error) {
      console.log("[follow-up-automation] WORKER ERROR:", error);
    }
  },
  { connection: redisConnection },
);

console.log("Follow-up Automation Worker Running");