import connectDB from "@/lib/db";
import Lead from "@/modules/leads/leads.model";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  await connectDB();

  const { searchParams } = new URL(req.url);
  const days = parseInt(searchParams.get("days") || "7");

  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - days);

  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

  const newCount = await Lead.countDocuments({
    createdAt: { $gte: oneWeekAgo },
  });
  const contactedCount = await Lead.countDocuments({
    createdAt: { $gte: fromDate, $lt: oneWeekAgo },
  });

  const to = new Date();
  return NextResponse.json({
    data: [
      { status: "new", count: newCount },
      { status: "contacted", count: contactedCount },
    ],
    date_range: {
      from: fromDate.toISOString().split("T")[0],
      to: to.toISOString().split("T")[0],
    },
  });
}