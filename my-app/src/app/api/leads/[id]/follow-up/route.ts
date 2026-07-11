import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";
import { sendManualFollowUpEmail } from "@/modules/leads/manualFollowUp.service";

type Params = { params: Promise<{ id: string }> };

export async function POST(
  req: NextRequest,
  { params }: Params,
) {
  try {
    await connectDB();
    const { id } = await params;
    const { force } = await req.json().catch(() => ({ force: false }));

    const result = await sendManualFollowUpEmail(id, !!force);

    return NextResponse.json({ success: true, ...result }, { status: 200 });
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : "Failed to send follow-up email";

    return NextResponse.json(
      { success: false, message },
      { status: 400 },
    );
  }
}
