import connectDB from "@/lib/db";
import { NextRequest } from "next/server";

import {
  getTemplateByIdController,
  updateTemplateController,
  deleteTemplateController,
} from "@/modules/Email/template.controller";

type Params = {
  params: Promise<{ id: string }>;
};

export async function GET(req: NextRequest, context: Params) {
  await connectDB();

  return getTemplateByIdController(req, context);
}

export async function PATCH(req: NextRequest, context: Params) {
  await connectDB();

  return updateTemplateController(req, context);
}

export async function DELETE(req: NextRequest, context: Params) {
  await connectDB();

  return deleteTemplateController(req, context);
}
