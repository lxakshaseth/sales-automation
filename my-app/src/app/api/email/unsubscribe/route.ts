import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";

import EmailEvent from "@/modules/Email/emailEvent.model";
import Unsubscribed from "@/modules/Email/unsubscribed.model";

export async function GET(req: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(req.url);

    const email = searchParams.get("email");
    const emailId = searchParams.get("emailId");

    if (!email || !emailId) {
      return NextResponse.json(
        { message: "Missing parameters" },
        { status: 400 }
      );
    }

    await EmailEvent.create({
      emailId,
      type: "UNSUBSCRIBE",
      metadata: {
        email,
      },
    });

    await Unsubscribed.findOneAndUpdate(
      { email },
      { email },
      { upsert: true, new: true }
    );

    return NextResponse.json({
      message: "You have successfully unsubscribed",
    });
  } catch (error) {
    console.error("UNSUBSCRIBE ERROR:", error);

    return NextResponse.json(
      {
        message: "Unsubscribe failed",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}