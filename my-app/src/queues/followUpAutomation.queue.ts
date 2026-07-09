import { Queue } from "bullmq";
import { redisConnection } from "./redis";

export const FOLLOW_UP_JOB_NAME = "run-follow-up-automation";
export const FOLLOW_UP_REPEAT_JOB_ID = "follow-up-automation-cron";
const FIFTEEN_MINUTES_MS = 15 * 60 * 1000;

export const followUpAutomationQueue = new Queue("followUpAutomationQueue", {
  connection: redisConnection,
});

export const scheduleFollowUpAutomationCron = async () => {
  await followUpAutomationQueue.add(
    FOLLOW_UP_JOB_NAME,
    {},
    {
      repeat: { every: FIFTEEN_MINUTES_MS },
      jobId: FOLLOW_UP_REPEAT_JOB_ID,
      removeOnComplete: true,
      removeOnFail: 50,
    },
  );
  console.log("Follow-up Automation Cron Scheduled (every 15 minutes)");
};