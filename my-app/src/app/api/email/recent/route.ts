import { NextResponse } from "next/server";
import connectDB from "@/lib/db";
import Email from "@/modules/Email/email.model";

export async function GET() {
  try {
    await connectDB();

    const recentEmails = await Email.find()
      .sort({ createdAt: -1 })
      .limit(5)
      .select("to subject status createdAt");

    return NextResponse.json({ recentEmails }, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { message: "Failed to fetch recent emails" },
      { status: 500 },
    );
  }
}
