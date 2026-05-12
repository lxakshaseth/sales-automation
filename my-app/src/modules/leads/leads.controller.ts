import Lead from "./leads.model"
import { NextRequest, NextResponse } from "next/server";
import "@/modules/campaign/campaign.model";
import mongoose from "mongoose";
import { DateTime } from "luxon"
type Params = { params: Promise<{ id: string; }>; };
const countryTimezoneMap: Record<string, string> = {
  usa: "America/New_York",

  india: "Asia/Kolkata",

  dubai: "Asia/Dubai",

  europe: "Europe/London",
};

export const createLeadController = async (
  req: NextRequest
) => {

  try {

    const body = await req.json();

    const timezone =countryTimezoneMap[body.country] || "UTC";

    const createLead = await Lead.create({...body,timezone,});

    const currentTime = DateTime.now().setZone(createLead.timezone).toString();

    const leadWithTime = {...createLead.toObject(),currentLocalTime: currentTime,};

    return NextResponse.json({success: true, data: leadWithTime,},{status: 201, });

  } catch (error: any) {

    return NextResponse.json(
      {
        success: false,
        message: error.message,
      },
      {
        status: 500,
      }
    );
  }
};

export const getLeadsController = async (req: NextRequest) => {
  try {

    const leads = await Lead.find().populate("campaign");
    const usaTime = DateTime.now()
      .setZone("America/New_York");

    console.log(usaTime.toString());

    return NextResponse.json({ success: true, count: leads.length, data: leads, }, { status: 200 });

  } catch (error: any) {

    return NextResponse.json({ success: false, message: error.message, }, { status: 500 });

  }
};