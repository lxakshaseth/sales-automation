import { NextRequest, NextResponse } from "next/server";
import Campaign from "./campaign.model";
import mongoose from "mongoose";
type Params = { params: Promise<{ id: string; }>; };

export const createCampaignController = async (req: NextRequest) => {
  try {
    const body = await req.json();
    const campaign = await Campaign.create(body);
    return NextResponse.json({ success: true, data: campaign, }, { status: 201, },);
  } catch (error: any) {
    return NextResponse.json({ success: false, message: error.message, }, { status: 500, },);
  }
}

export const getCampaignsController = async (req: NextRequest) => {
  try {
    const { searchParams } = new URL(req.url);
    const page = Number(searchParams.get("page")) || 1;
    const limit = Number(searchParams.get("limit")) || 10;
    const skip = (page - 1) * limit;

    const campaigns = await Campaign.find(searchParams).sort({ createdAt: -1, }).skip(skip).limit(limit);
    const count = await Campaign.countDocuments();
    return NextResponse.json({
      success: true,
      page: page,
      limit: limit,
      totalData: count,
      data: campaigns,
    },
      { status: 200, },);

  } 
  
  catch (error: any) {
    return NextResponse.json({ success: false, message: error.message, }, { status: 500, },);
  }
}
export const getCampaignByIdController = async (req: NextRequest, context: Params) => {

  try {

    const { id } = await context.params;

     if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json({ success: false, message: "Invalid campaign id", }, { status: 400 });
    }

    const campaign = await Campaign.findById(id);
    if (!campaign) {
      return NextResponse.json({ success: false, message: "Campaign not found", }, { status: 404, });
    }
    return NextResponse.json({ success: true, data: campaign, }, { status: 200, });

  }
  
  catch (error: any) {
    return NextResponse.json({ success: false, message: error.message, }, { status: 500, });
  }
};

export const updateCampaignController = async (req: NextRequest, context: Params) => {
  try {

    const { id } = await context.params;
    
     if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json({ success: false, message: "Invalid campaign id", }, { status: 400 });
    }
    const body = await req.json();
    const updatedCampaign = await Campaign.findByIdAndUpdate(id, body);
    if (!updatedCampaign) {
      return NextResponse.json({ success: false, msg: "Campaign not found" }, { status: 404 })
    };


    return NextResponse.json(
      {
        success: true,
        message: "Campaign updated successfully",
        
      },
      {
        status: 200,
      },
    );
  } 
  
  catch (error: any) {
    return NextResponse.json({ success: false, message: error.message, }, { status: 500, });
  }
}

export const deleteCampaingnController = async (req: NextRequest, context: Params) => {
  try {
    const { id } = await context.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return NextResponse.json({ success: false, message: "Invalid campaign id", }, { status: 400 });
    }
    const deleteCampaingn = await Campaign.findByIdAndDelete(id);

    if (!deleteCampaingn) {
      return NextResponse.json({ success: true, message: "Campaign not found" }, { status: 200 });
    }
    return NextResponse.json({ success: true, message: "Deleted successfully" }, { status: 200 });

  } 
  
  catch (error: any) {
    return NextResponse.json({ success: false, message: error.message, }, { status: 500, });
  }
}
