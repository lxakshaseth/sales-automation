import { loginController } from "@/modules/auth/auth.controller";
import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";

export const POST = async (req: NextRequest) => {
  try {
    await connectDB();
    return loginController(req);
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Login failed";

    return NextResponse.json({ success: false, message }, { status: 500 });
  }
};
