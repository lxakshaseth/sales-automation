import connectDB from "@/lib/db";
import { getDashboardStatsController } from "@/modules/dashboard/dashboard.controller";

export async function GET() {
  await connectDB();

  return getDashboardStatsController();
}