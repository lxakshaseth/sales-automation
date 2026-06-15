import connectDB from "@/lib/db";
import { NextRequest } from "next/server";

import {
  createTemplateController,
  getTemplatesController,
} from "@/modules/Email/template.controller";

export async function POST(req: NextRequest) {
  await connectDB();

  return createTemplateController(req);
}

export async function GET() {
  await connectDB();

  return getTemplatesController();
}