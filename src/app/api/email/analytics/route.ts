import { NextResponse } from "next/server";

import connectDB from "@/lib/db";

import Email from "@/modules/Email/email.model";
import EmailEvent from "@/modules/Email/emailEvent.model";
import Unsubscribed from "@/modules/Email/unsubscribed.model";

export async function GET() {
  try {
    await connectDB();

    // Total emails
    const totalEmails = await Email.countDocuments();

    // Sent emails
    const sentEmails = await Email.countDocuments({
      status: "SENT",
    });

    // Failed emails
    const failedEmails = await Email.countDocuments({
      status: "FAILED",
    });

    // Total clicks
    const totalClicks = await EmailEvent.countDocuments({
      type: "CLICK",
    });

    // Total unsubscribed users
    const totalUnsubscribed =
      await Unsubscribed.countDocuments();

    // Click Through Rate
    const clickThroughRate =
      sentEmails > 0
        ? ((totalClicks / sentEmails) * 100).toFixed(2)
        : "0";

    return NextResponse.json(
      {
        totalEmails,
        sentEmails,
        failedEmails,
        totalClicks,
        totalUnsubscribed,
        clickThroughRate: `${clickThroughRate}%`,
      },
      { status: 200 },
    );
  } catch (error) {
    return NextResponse.json(
      {
        message: "Failed to fetch analytics",
        error:
          error instanceof Error
            ? error.message
            : "Unknown error",
      },
      { status: 500 },
    );
  }
}