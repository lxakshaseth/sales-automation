import connectDB from "@/lib/db";
import { getDashboardStatsController } from "@/modules/dashboard/dashboard.controller";
import { NextResponse } from "next/server";

export async function GET() {
  try {
    await connectDB();

    return getDashboardStatsController();
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch dashboard stats";

    return NextResponse.json(
      {
        success: false,
        message,
      },
      {
        status: 500,
      },
    );
  }
}
