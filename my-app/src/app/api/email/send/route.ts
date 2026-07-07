import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";

import "@/queues/redis";

import { emailQueue } from "@/queues/email.queue";

export async function POST(req: NextRequest) {
  try {
    await connectDB();

    const body = await req.json();

    await emailQueue.add("send-email", body);

    return NextResponse.json(
      {
        message: "Email job added to queue successfully",
      },
      { status: 201 },
    );
  } catch (error) {
    return NextResponse.json(
      {
        message: "Failed to add email job",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    );
  }
}
