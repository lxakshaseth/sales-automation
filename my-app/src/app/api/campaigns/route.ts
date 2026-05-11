import { connectDB } from "@/lib/db";
import { NextRequest } from "next/server";

import {
  createCampaignController,
  getCampaignsController,
} from "@/modules/campaign/campaign.controller";

export async function POST(req: NextRequest) {
  await connectDB();

  return createCampaignController(req);
}

export async function GET(req: NextRequest) {
  await connectDB();

  return getCampaignsController(req);
}


