import { NextRequest, NextResponse } from "next/server";
import { sendEmail } from "@/modules/Email/email.controller";
import connectDB from "@/lib/db";

export async function POST(req: NextRequest) {
  try {
    await connectDB();

    const body = await req.json();

    const email = await sendEmail(body);

    return NextResponse.json(
      {
        message: "Email sent successfully",
        data: email,
      },
      { status: 201 },
    );
  } catch (error) {
    return NextResponse.json(
      {
        message: "Failed to send email",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}