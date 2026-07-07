import { bulkUploadLeadController } from "@/modules/leads/bulkLeadUpload.controller";
import { NextRequest } from "next/server";
import connectDB from "@/lib/db";

export async function POST(req: NextRequest) {
  await connectDB();
  return bulkUploadLeadController(req);
}
