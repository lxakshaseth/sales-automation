import dotenv from "dotenv";

dotenv.config({
  path: ".env",
});

import "./email.worker";
import "./whatsapp-lifecycle.worker";
import "./campaignAutomation.worker";
import "./followUpAutomation.worker";


import { scheduleCampaignAutomationCron } from "./campaignAutomation.queue";
import { scheduleFollowUpAutomationCron } from "./followUpAutomation.queue";


void scheduleCampaignAutomationCron().catch((error) => {
  console.error("Failed to schedule campaign automation cron:", error);
});

void scheduleFollowUpAutomationCron().catch(console.error);

// import "./email.queue"; --> This will clear the queue every time the worker starts.
