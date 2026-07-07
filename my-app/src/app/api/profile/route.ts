import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";
import User from "@/modules/auth/user.model";
import jwt from "jsonwebtoken";

const getAuthUserIdFromRequest = (req: NextRequest) => {
  const authHeader = req.headers.get("authorization") || "";
  const token = authHeader.startsWith("Bearer ")
    ? authHeader.slice("Bearer ".length)
    : "";

  if (!token) return null;

  try {
    const decoded = jwt.verify(token, process.env.jwt_secret as string);
    const payload = decoded as { id?: unknown };
    return payload?.id ? String(payload.id) : null;
  } catch {
    return null;
  }
};

export async function GET(req: NextRequest) {
  await connectDB();

  const userId = getAuthUserIdFromRequest(req);
  if (!userId) {
    return NextResponse.json(
      { success: false, message: "Unauthorized" },
      { status: 401 },
    );
  }

  const user = await User.findById(userId).lean();
  if (!user) {
    return NextResponse.json(
      { success: false, message: "User not found" },
      { status: 404 },
    );
  }

  return NextResponse.json({
    success: true,
    data: {
      name: user.name || "",
      email: user.email || "",
      phoneNumber: (user as { mobile?: string }).mobile || "",
      companyName: (user as { companyName?: string }).companyName || "",
      role: "Administrator",
      memberSince: user.createdAt
        ? new Date(user.createdAt).toLocaleDateString("en-GB", {
            day: "2-digit",
            month: "long",
            year: "numeric",
          })
        : "",
    },
  });
}

export async function PUT(req: NextRequest) {
  await connectDB();

  const userId = getAuthUserIdFromRequest(req);
  if (!userId) {
    return NextResponse.json(
      { success: false, message: "Unauthorized" },
      { status: 401 },
    );
  }

  const body = await req.json();
  const { name, email, mobile, companyName } = body || {};

  // Minimal server-side validation (UI also validates)
  const nameStr = String(name ?? "").trim();
  const emailStr = String(email ?? "").trim();
  const mobileStr = String(mobile ?? "").trim();

  if (!nameStr) {
    return NextResponse.json(
      { success: false, message: "Full Name is required" },
      { status: 400 },
    );
  }
  if (!/^[A-Za-z ]+$/.test(nameStr) || nameStr.length < 2) {
    return NextResponse.json(
      { success: false, message: "Invalid Full Name" },
      { status: 400 },
    );
  }
  if (!emailStr) {
    return NextResponse.json(
      { success: false, message: "Email is required" },
      { status: 400 },
    );
  }
  if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(emailStr)) {
    return NextResponse.json(
      { success: false, message: "Enter a valid email" },
      { status: 400 },
    );
  }
  if (!/^\d{10}$/.test(mobileStr)) {
    return NextResponse.json(
      { success: false, message: "Enter a valid 10-digit number" },
      { status: 400 },
    );
  }

  const updatePayload: {
    name: string;
    email: string;
    mobile: string;
    companyName?: string;
  } = {
    name: nameStr,
    email: emailStr,
    mobile: mobileStr,
  };

  if (companyName !== undefined) {
    updatePayload.companyName = String(companyName ?? "").trim();
  }

  const updated = await User.findByIdAndUpdate(
    userId,
    {
      $set: updatePayload,
    },
    { new: true },
  ).lean();

  if (!updated) {
    return NextResponse.json(
      { success: false, message: "User not found" },
      { status: 404 },
    );
  }

  return NextResponse.json({
    success: true,
    message: "Profile updated successfully",
  });
}
