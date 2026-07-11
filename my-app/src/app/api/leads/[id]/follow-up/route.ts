import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";
import { sendManualFollowUpEmail } from "@/modules/leads/manualFollowUp.service";

export async function POST(
  req: NextRequest,
  { params }: { params: { id: string } },
) {
  try {
    await connectDB();
    const { force } = await req.json().catch(() => ({ force: false }));

    const result = await sendManualFollowUpEmail(params.id, !!force);

    return NextResponse.json({ success: true, ...result }, { status: 200 });
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 400 },
    );
  }
}