import Lead from "./leads.model";
import Campaign from "../campaign/campaign.model";
import { NextRequest, NextResponse } from "next/server";
import csv from "csv-parser";
import { Readable } from "stream";
import { startCampaignFlow } from "@/modules/automation/automation.service";

const countryTimezoneMap: Record<string, any> = {
  india: "Asia/Kolkata",
  dubai: "Asia/Dubai",
  europe: "Europe/London",
};

export const bulkUploadLeadController = async (req: NextRequest) => {
  try {
    const formData = await req.formData();   
    const file = formData.get("file") as File;

    if (!file) {
      return NextResponse.json({success: false,message: "CSV file required",},{ status: 400 },);
    }

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    const results: any[] = [];

    await new Promise((resolve, reject) => {
      Readable.from(buffer).pipe(csv()).on("data", (data) => {
          results.push(data);
        })
        .on("end", resolve)
        .on("error", reject);
    });

    const insertedLeads = [];

    for (const row of results) {
      const {
        firstName,
        lastName,
        email,
        phone,
        company,
        country,
        state,
        campaign,
      } = row;

      if (!email || !campaign) {
        continue;
      }

      const campaignExists = await Campaign.exists({
        _id: campaign,
      });
     
      

      if (!campaignExists) {
        continue;
      }

      const existingLead = await Lead.exists({ email });

      if (existingLead) {
        continue;
      }

      const countryData =
        countryTimezoneMap[country?.toLowerCase()];

      const timezone =
        typeof countryData === "string"
          ? countryData
          : countryData?.[state?.toLowerCase()];

      const lead = await Lead.create({
        firstName,
        lastName,
        email,
        phone,
        company,
        country,
        state,
        campaign,
        timezone,
      });

      insertedLeads.push(lead);

      await startCampaignFlow(lead._id.toString());
    }

    return NextResponse.json(
      {
        success: true,
        totalUploaded: insertedLeads.length,
        data: insertedLeads,
      },
      { status: 201 },
    );
  } catch (error: any) {
    return NextResponse.json(
      {
        success: false,
        message: error.message,
      },
      { status: 500 },
    );
  }
};