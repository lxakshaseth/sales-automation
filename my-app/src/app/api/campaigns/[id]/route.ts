import { connectDB } from "@/lib/db";
import { getCampaignByIdController, updateCampaignController } from "@/modules/campaign/campaign.controller";
import { NextRequest } from "next/server";
type Params = { params: Promise<{ id: string; }>; };

export async function GET(req: NextRequest, context: Params) {
  await connectDB();
  return getCampaignByIdController(req, context);
}

export async function PATCH(req: NextRequest, context: Params,) {
  await connectDB();
  return updateCampaignController(req, context);
}
