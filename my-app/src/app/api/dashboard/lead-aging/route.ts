import Lead from "@/modules/leads/leads.model";
import connectDB from "@/lib/db";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    await connectDB();

    const leads = await Lead.find()
      .sort({ stageEnteredAt: -1 })
      .limit(10);

    const result = leads.map((lead: any) => ({
      id: lead._id,
      name: `${lead.firstName} ${lead.lastName ?? ""}`.trim(),
      company: lead.company || "—",
      stage: lead.status,
      lastActivity: lead.lastActivity || "Lead Created",
      agingDays: Math.floor(
        (Date.now() - new Date(lead.stageEnteredAt || lead.createdAt).getTime()) /
        (1000 * 60 * 60 * 24)
      ),
      email: lead.email,
    }));

    return NextResponse.json({ success: true, data: result }, { status: 200 });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 }
    );
  }
}