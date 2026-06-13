import { Queue } from "bullmq";
import { redisConnection } from "./redis";

export const emailQueue = new Queue("emailQueue", {
  connection: redisConnection,
});

// emailQueue.obliterate({ force: true });
// console.log("Queue Cleared");

console.log("Email Queue Ready");