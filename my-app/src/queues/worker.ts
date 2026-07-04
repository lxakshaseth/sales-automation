import dotenv from "dotenv";

dotenv.config({
  path: ".env",
});

import "./email.worker";
import "./whatsapp-lifecycle.worker";
import "./campaignAutomation.worker";

import { scheduleCampaignAutomationCron } from "./campaignAutomation.queue";

void scheduleCampaignAutomationCron().catch((error) => {
  console.error("Failed to schedule campaign automation cron:", error);
});