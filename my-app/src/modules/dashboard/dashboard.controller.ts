import { NextResponse } from "next/server";
import { getDashboardStats } from "./dashboard.service";

export async function getDashboardStatsController() {
  try {
    const stats = await getDashboardStats();

    return NextResponse.json(
      {
        success: true,
        data: stats,
      },
      {
        status: 200,
      }
    );
  } catch (error: any) {
    return NextResponse.json(
      {
        success: false,
        message: error.message,
      },
      {
        status: 500,
      }
    );
  }
}