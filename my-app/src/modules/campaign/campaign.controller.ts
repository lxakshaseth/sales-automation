import { NextRequest, NextResponse } from "next/server";
import Campaign from "./campaign.model";
import mongoose from "mongoose";
import { createAuditLog } from "@/modules/audit-log/auditLog.service";
type Params = { params: Promise<{ id: string }> };

export const createCampaignController = async (req: NextRequest) => {
  try {
    const body = await req.json();

    const existing = await Campaign.findOne({
      name: { $regex: `^${body.name.trim()}$`, $options: "i" },
    });
    if (existing) {
      return NextResponse.json(
        { success: false, message: "A campaign with this name already exists." },
        { status: 409 }
      );
    }

    const campaign = await Campaign.create(body);
    await createAuditLog("Campaigns", "Create", campaign.name, "Campaign created");

    return NextResponse.json({ success: true, data: campaign }, { status: 201 });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 }
    );
  }
};

export const getCampaignsController = async (req: NextRequest) => {
  try {
    const { searchParams } = new URL(req.url);
    const page = Number(searchParams.get("page")) || 1;
    const limit = Number(searchParams.get("limit")) || 10;
    const skip = (page - 1) * limit;
    const name = searchParams.get("name");
    const description = searchParams.get("description");
    const status = searchParams.get("status");

    const filter: any = {};
    if (name) {
      filter.name = { $regex: name, $options: "i" };
    }
    if (description) {
      filter.description = { $regex: description, $options: "i" };
    }
    if (status) {
      filter.status = { $regex: status, $options: "i" };
    }

    const campaigns = await Campaign.find(filter)
      .populate("emailTemplates")
      .populate("smsTemplates")
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);
    const count = await Campaign.countDocuments(filter);
    return NextResponse.json(
      {
        success: true,
        page: page,
        limit: limit,
        totalData: count,
        data: campaigns,
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
export const getCampaignByIdController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        { success: false, message: "Invalid campaign id" },
        { status: 400 },
      );
    }

    const campaign = await Campaign.findById(id)
      .populate("emailTemplates")
      .populate("smsTemplates");
    if (!campaign) {
      return NextResponse.json(
        { success: false, message: "Campaign not found" },
        { status: 404 },
      );
    }
    return NextResponse.json(
      { success: true, data: campaign },
      { status: 200 },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};

export const updateCampaignController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        { success: false, message: "Invalid campaign id" },
        { status: 400 },
      );
    }
    const body = await req.json();

    const oldCampaign = await Campaign.findById(id);

    if (body.name && body.name.trim()) {
      const existing = await Campaign.findOne({
        _id: { $ne: id },
        name: { $regex: `^${body.name.trim()}$`, $options: "i" },
      });
      if (existing) {
        return NextResponse.json(
          { success: false, message: "A campaign with this name already exists." },
          { status: 409 }
        );
      }
    }

    const updatedCampaign = await Campaign.findByIdAndUpdate(
      id,
      body,
      { new: true }
    );

    let details = "Campaign updated";

    if (body.name && oldCampaign?.name !== body.name) {
      details = "Name changed";
    }
    else if (body.status && oldCampaign?.status !== body.status) {
      details = `Status changed ${oldCampaign.status} → ${body.status}`;
    }
    else if (
      body.description &&
      oldCampaign?.description !== body.description
    ) {
      details = "Description updated";
    }

    await createAuditLog(
      "Campaign",
      "Update",
      updatedCampaign?.name || oldCampaign?.name,
      details
    );

    if (!updatedCampaign) {
      return NextResponse.json(
        { success: false, msg: "Campaign not found" },
        { status: 404 },
      );
    }

    return NextResponse.json(
      {
        success: true,
        message: "Campaign updated successfully",
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

export const deleteCampaingnController = async (
  req: NextRequest,
  context: Params,
) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json(
        { success: false, message: "Invalid campaign id" },
        { status: 400 },
      );
    }
    const deleteCampaingn = await Campaign.findByIdAndDelete(id);

    if (!deleteCampaingn) {
      return NextResponse.json(
        { success: true, message: "Campaign not found" },
        { status: 200 },
      );
    }

    await createAuditLog(
      "Campaigns",
      "Delete",
      deleteCampaingn.name,
      "Campaign removed"
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
