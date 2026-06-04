import connectDB from "@/lib/db";

import { NextRequest } from "next/server";

import { assignSingleLeadController } from "@/modules/automation/automation.controller";

export async function POST(
  req: NextRequest,
) {
  await connectDB();

  return assignSingleLeadController(req);
}