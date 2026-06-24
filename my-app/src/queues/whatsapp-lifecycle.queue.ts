import { Queue } from "bullmq";

import { redisConnection } from "./redis";

export type WhatsAppLifecycleJobData = {
  contactId: string;
  runId: string;
};

export const whatsappLifecycleQueue = new Queue<WhatsAppLifecycleJobData>(
  "whatsappLifecycleQueue",
  {
    connection: redisConnection,
  },
);

console.log("WhatsApp Lifecycle Queue Ready");
