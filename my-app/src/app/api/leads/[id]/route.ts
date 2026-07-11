import connectDB from "@/lib/db";
import {
  getLeadsByIdController,
  updateLeadController,
  deleteLeadController,
} from "@/modules/leads/leads.controller";
import { NextRequest } from "next/server";

type Params = { params: Promise<{ id: string }> };

export async function GET(req: NextRequest, context: Params) {
  await connectDB();
  return getLeadsByIdController(req, context);
}

export async function PATCH(req: NextRequest, context: Params) {
  await connectDB();
  return updateLeadController(req, context);
}

export async function PUT(req: NextRequest, context: Params) {
  await connectDB();
  return updateLeadController(req, context);
}

export async function DELETE(req: NextRequest, context: Params) {
  await connectDB();
  return deleteLeadController(req, context);
}
