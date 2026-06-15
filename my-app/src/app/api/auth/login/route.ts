import { loginController } from "@/modules/auth/auth.controller";
import { NextRequest } from "next/server";
import connectDB from "@/lib/db";

export const POST = async (req: NextRequest) => {
     await connectDB();
    return loginController(req as any)
}