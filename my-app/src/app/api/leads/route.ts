import  connectDB  from "@/lib/db";
import { NextRequest } from "next/server";

import {createLeadController,getLeadsController} from "@/modules/leads/leads.controller";

export async function POST(req: NextRequest) {
  await connectDB();

  return createLeadController(req);
}

export async function GET(req: NextRequest) {
  await connectDB();

  return getLeadsController(req);
}