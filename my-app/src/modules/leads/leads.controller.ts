import Lead from "./leads.model"
import { NextRequest, NextResponse } from "next/server";
import mongoose from "mongoose";
type Params = { params: Promise<{ id: string; }>; };

export const createLeadController=async(req:NextRequest)=>{
    try {
        const body=await req.json();
        const createLead=await Lead.create(body);
        return NextResponse.json({success:true,data:createLead},{status:201})
        
    } catch (error:any) {
         return NextResponse.json({ success: false, message: error.message, }, { status: 500, });
    }
}