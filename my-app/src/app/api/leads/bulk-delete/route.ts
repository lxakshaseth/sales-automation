import connectDB from "@/lib/db";
import { bulkDeleteLeadsController } from "@/modules/leads/leads.controller";
import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  await connectDB();
  return bulkDeleteLeadsController(req);
}
