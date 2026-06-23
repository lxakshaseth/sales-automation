import { NextResponse } from "next/server";
import connectDB from "@/lib/db";
import Email from "@/modules/Email/email.model";
import EmailEvent from "@/modules/Email/emailEvent.model";
import Unsubscribed from "@/modules/Email/unsubscribed.model";

export async function GET() {
  try {
    await connectDB();

    const totalEmails = await Email.countDocuments();
    const sentEmails = await Email.countDocuments({ status: "SENT" });
    const failedEmails = await Email.countDocuments({ status: "FAILED" });
    const totalClicks = await EmailEvent.countDocuments({ type: "CLICK" });
    const totalOpens = await EmailEvent.countDocuments({ type: "OPEN" });
    const totalUnsubscribed = await Unsubscribed.countDocuments();

    const clickThroughRate =
      sentEmails > 0
        ? ((totalClicks / sentEmails) * 100).toFixed(2)
        : "0";

    const openRate =
      sentEmails > 0
        ? ((totalOpens / sentEmails) * 100).toFixed(2)
        : "0";

    return NextResponse.json(
      {
        totalEmails,
        sentEmails,
        failedEmails,
        totalClicks,
        totalOpens,
        totalUnsubscribed,
        clickThroughRate: `${clickThroughRate}%`,
        openRate: `${openRate}%`,
      },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      {
        message: "Failed to fetch analytics",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}