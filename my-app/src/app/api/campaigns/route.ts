<<<<<<< HEAD
import { NextResponse } from "next/server";
import { connectDB } from "@/lib/db";
import Campaign from "@/modules/Campaign";

export async function POST(req: Request) {
  try {
    await connectDB();

    const body = await req.json();

    const campaign = await Campaign.create(body);

    return NextResponse.json(campaign, { status: 201 });
  } catch (error: any) {
    return NextResponse.json(
      { status: false, msg: error.message },
      { status: 500 }
    );
  }
}
export async function GET(req: Request) {
  try {
    await connectDB();
    const campaign = await Campaign.findOne();
    

    return NextResponse.json(campaign, { status: 201 });
  } catch (error: any) {
    return NextResponse.json(
      { status: false, msg: error.message },
      { status: 500 }
    );
  }
}

export async function getCampaigns(){
  
}
=======
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


>>>>>>> 3fd7123 (sync Campaign)
