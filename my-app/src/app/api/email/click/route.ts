import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";
import EmailEvent from "@/modules/Email/emailEvent.model";

export async function GET(req: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(req.url);

    const url = searchParams.get("url");
    const emailId = searchParams.get("emailId");

    if (!url || !emailId) {
      return NextResponse.json(
        { message: "Missing parameters" },
        { status: 400 }
      );
    }

    const decodedUrl = decodeURIComponent(url);

    const event = await EmailEvent.create({
      emailId,
      type: "CLICK",
      metadata: {
        url: decodedUrl,
        userAgent: req.headers.get("user-agent") || "",
      },
    });

    if (!event) {
      return NextResponse.json(
        { message: "Failed to store click event" },
        { status: 500 }
      );
    }

    return NextResponse.redirect(decodedUrl);
  } catch (error) {
    console.error("CLICK ERROR:", error);

    return NextResponse.json(
      {
        message: "Click tracking failed",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}