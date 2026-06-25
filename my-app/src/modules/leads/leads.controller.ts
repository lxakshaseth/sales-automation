import Lead from "./leads.model";
import { NextRequest, NextResponse } from "next/server";
import "@/modules/campaign/campaign.model";
import mongoose from "mongoose";
import { DateTime } from "luxon";
import { startCampaignFlow } from "@/modules/automation/automation.service";
import Campaign from "../campaign/campaign.model";
import { createAuditLog } from "@/modules/audit-log/auditLog.service";
type Params = { params: Promise<{ id: string }> };

const countryTimezoneMap: Record<string, any> = {
  usa: {
    alabama: "America/Chicago",
    alaska: "America/Anchorage",
    arizona: "America/Phoenix",
    arkansas: "America/Chicago",
    california: "America/Los_Angeles",
    colorado: "America/Denver",
    connecticut: "America/New_York",
    delaware: "America/New_York",
    florida: "America/New_York",
    georgia: "America/New_York",
    hawaii: "Pacific/Honolulu",
    idaho: "America/Denver",
    illinois: "America/Chicago",
    indiana: "America/Indiana/Indianapolis",
    iowa: "America/Chicago",
    kansas: "America/Chicago",
    kentucky: "America/New_York",
    louisiana: "America/Chicago",
    maine: "America/New_York",
    maryland: "America/New_York",
    massachusetts: "America/New_York",
    michigan: "America/Detroit",
    minnesota: "America/Chicago",
    mississippi: "America/Chicago",
    missouri: "America/Chicago",
    montana: "America/Denver",
    nebraska: "America/Chicago",
    nevada: "America/Los_Angeles",
    "new hampshire": "America/New_York",
    "new jersey": "America/New_York",
    "new mexico": "America/Denver",
    "new york": "America/New_York",
    "north carolina": "America/New_York",
    "north dakota": "America/Chicago",
    ohio: "America/New_York",
    oklahoma: "America/Chicago",
    oregon: "America/Los_Angeles",
    pennsylvania: "America/New_York",
    "rhode island": "America/New_York",
    "south carolina": "America/New_York",
    "south dakota": "America/Chicago",
    tennessee: "America/Chicago",
    texas: "America/Chicago",
    utah: "America/Denver",
    vermont: "America/New_York",
    virginia: "America/New_York",
    washington: "America/Los_Angeles",
    "west virginia": "America/New_York",
    wisconsin: "America/Chicago",
    wyoming: "America/Denver",
  },

  india: "Asia/Kolkata",
  dubai: "Asia/Dubai",
  europe: "Europe/London",
};

export const createLeadController = async (req: NextRequest) => {
  try {
    const body = await req.json();
    const { country, state, campaign, email } = body;

    const campaignExists = await Campaign.exists({ _id: campaign });
    if (!campaignExists)
      return NextResponse.json(
        { success: false, message: "Campaign not found" },
        { status: 404 },
      );

    const checkLeadEmail = await Lead.exists({ email });

    if (checkLeadEmail) {
      return NextResponse.json(
        { success: false, message: "email is already exists" },
        { status: 409 },
      );
    }

    const countryData = countryTimezoneMap[country?.toLowerCase()];
    const timezone =
      typeof countryData === "string"
        ? countryData
        : countryData?.[state?.toLowerCase()];

    const createLead = await Lead.create({
      ...body,
      timezone,
      stageEnteredAt: new Date(),
      lastActivity: "Lead Created",
      });
      
      const leadName =
      `${createLead.firstName || ""} ${createLead.lastName || ""}`.trim();

       await createAuditLog(
        "Leads",
        "Create",
        leadName,
       "Lead created"
      );

    // await startCampaignFlow(createLead._id.toString());

    const currentTime = DateTime.now().setZone(createLead.timezone).toString();

    const leadWithTime = {
      ...createLead.toObject(),
      currentLocalTime: currentTime,
    };

    return NextResponse.json(
      { success: true, data: leadWithTime },
      { status: 201 },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};

export const getLeadsController = async (req: NextRequest) => {
  try {
    const { searchParams } = new URL(req.url);
    const page = Number(searchParams.get("page")) || 1;
    const limit = Number(searchParams.get("limit")) || 10;
    const skip = (page - 1) * limit;
    const firstName = searchParams.get("firstName");
    const email = searchParams.get("email");
    const lastName = searchParams.get("lastName");
    const phone = searchParams.get("phone");
    const company = searchParams.get("company");
    const country = searchParams.get("country");
    const state = searchParams.get("state");
    const filter: any = {};

    if (firstName) {
      filter.firstName = { $regex: firstName, $options: "i" };
    }
    if (email) {
      filter.email = { $regex: email, $options: "i" };
    }
    if (lastName) {
      filter.lastName = { $regex: lastName, $options: "i" };
    }
    if (phone) {
      filter.phone = { $regex: phone, $options: "i" };
    }
    if (company) {
      filter.company = { $regex: company, $options: "i" };
    }
    if (country) {
      filter.country = { $regex: country, $options: "i" };
    }
    if (state) {
      filter.state = { $regex: state, $options: "i" };
    }

    const leads = await Lead.find(filter)
      .populate("campaign")
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);
    
    const leadsWithAging = leads.map(
        (lead: any) => {
          const agingDays = Math.floor(
            (
              Date.now() -
              new Date(
                lead.stageEnteredAt ||
                lead.createdAt
              ).getTime()
            ) /
            (1000 * 60 * 60 * 24)
          );

          return {
            ...lead.toObject(),
            agingDays,
          };
        }
      );
    const totalData = await Lead.countDocuments(filter);
    return NextResponse.json(
      {
        success: true,
        page: page,
        limit: limit,
        totalData: totalData,
        data: leads,
      },
      { status: 200 },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};

export const getLeadsByIdController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;
    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        { success: false, message: "invalid lead id" },
        { status: 400 },
      );
    }
    const lead = await Lead.findById(id).populate("campaign");
    if (!lead) {
      return NextResponse.json(
        { success: false, message: "lead not found" },
        { status: 404 },
      );
    }
    return NextResponse.json({ success: true, data: lead }, { status: 200 });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};

export const updateLeadController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        { success: false, message: "Invalid lead id" },
        { status: 400 },
      );
    }
    const body = await req.json();
    const existingLead = await Lead.findById(id);

      if (!existingLead) {
        return NextResponse.json(
          {
            success: false,
            message: "Lead not found",
          },
          { status: 404 }
        );
      }

      if (
        body.status &&
        body.status !== existingLead.status
      ) {
        body.stageEnteredAt = new Date();

        body.lastActivity =
          `Moved from ${existingLead.status} to ${body.status}`;
      }
    const updatedLead = await Lead.findByIdAndUpdate(
      id,
      body,
      { new: true, runValidators: true }
    );

    const changes: string[] = [];

      if (
        existingLead.firstName !== updatedLead.firstName ||
        existingLead.lastName !== updatedLead.lastName
      ) {
        changes.push("Name changed");
      }

      if (existingLead.email !== updatedLead.email) {
        changes.push("Email updated");
      }

      if (existingLead.phone !== updatedLead.phone) {
        changes.push("Phone updated");
      }

      if (existingLead.status !== updatedLead.status) {
        changes.push(
          `Status changed ${existingLead.status} → ${updatedLead.status}`
        );
      }

      if (existingLead.source !== updatedLead.source) {
        changes.push(
          `Source changed ${existingLead.source} → ${updatedLead.source}`
        );
      }

      if (existingLead.score !== updatedLead.score) {
        changes.push("Lead score updated");
      }

      const details =
        changes.length > 0
          ? changes.join(", ")
          : "Lead updated";

      const leadName =
        `${updatedLead.firstName || ""} ${updatedLead.lastName || ""}`.trim();

      await createAuditLog(
        "Leads",
        "Update",
        leadName,
        details
      );

      if (!updatedLead) {
      return NextResponse.json(
        { success: false, msg: "lead not found" },
        { status: 404 },
      );
    }

    return NextResponse.json(
      {
        success: true,
        message: "lead updated successfully",
      },
      {
        status: 200,
      },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};

export const deleteLeadController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        { success: false, message: "Invalid lead id" },
        { status: 400 },
      );
    }
    const deleteLead = await Lead.findByIdAndDelete(id);

    if (!deleteLead) {
      return NextResponse.json(
        { success: true, message: "lead not found" },
        { status: 200 },
      );
    }

    const leadName =
    `${deleteLead.firstName || ""} ${deleteLead.lastName || ""}`.trim();

      await createAuditLog(
        "Leads",
        "Delete",
        leadName,
        "Lead removed"
      );

    return NextResponse.json(
      { success: true, message: "Deleted successfully" },
      { status: 200 },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};
