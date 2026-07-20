import { Worker } from "bullmq";

import { redisConnection } from "./redis";

import { sendEmail } from "@/modules/Email/email.controller";
import Lead from "@/modules/leads/leads.model";

import connectDB from "@/lib/db";

export const emailWorker = new Worker(
  "emailQueue",

  async (job) => {
    try {
      console.log("Processing Job:", job.id);

      await connectDB();

      console.log("MongoDB Connected In Worker");

      const result = await sendEmail(job.data);
      if (job.data?.leadId && result?.status === "SENT") {
        await Lead.findByIdAndUpdate(job.data.leadId, {
          lastEmailSentAt: new Date(),
        });
      }

      console.log("Email Sent Successfully");
    } catch (error) {
      console.log("WORKER ERROR:", error);
    }
  },

  {
    connection: redisConnection,
  },
);

console.log("Email Worker Running");