import { Worker } from "bullmq";

import connectDB from "@/lib/db";
import {
  processCloseChatJob,
  processReminderJob,
} from "@/modules/whatsapp/conversation-lifecycle.service";

import { redisConnection } from "./redis";

export const whatsappLifecycleWorker = new Worker(
  "whatsappLifecycleQueue",
  async (job) => {
    await connectDB();

    if (job.name === "send-reminder") {
      await processReminderJob(job.data.contactId, job.data.runId);
      return;
    }

    if (job.name === "close-chat") {
      await processCloseChatJob(job.data.contactId, job.data.runId);
    }
  },
  {
    connection: redisConnection,
  },
);

console.log("WhatsApp Lifecycle Worker Running");
