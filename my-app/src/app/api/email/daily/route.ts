import { NextResponse } from "next/server";
import connectDB from "@/lib/db";
import Email from "@/modules/Email/email.model";

export async function GET() {
  try {
    await connectDB();

    const last7Days = await Email.aggregate([
      {
        $match: {
          createdAt: {
            $gte: new Date(
              Date.now() - 7 * 24 * 60 * 60 * 1000
            ),
          },
        },
      },
      {
        $group: {
          _id: {
            $dateToString: {
              format: "%Y-%m-%d",
              date: "$createdAt",
            },
          },
          sent: {
            $sum: {
              $cond: [{ $eq: ["$status", "SENT"] }, 1, 0],
            },
          },
          failed: {
            $sum: {
              $cond: [{ $eq: ["$status", "FAILED"] }, 1, 0],
            },
          },
          pending: {
            $sum: {
              $cond: [{ $eq: ["$status", "PENDING"] }, 1, 0],
            },
          },
        },
      },
      { $sort: { _id: 1 } },
    ]);

    return NextResponse.json(
      { last7Days },
      { status: 200 }
    );
  } catch (error) {
    return NextResponse.json(
      { message: "Failed to fetch daily stats" },
      { status: 500 }
    );
  }
}