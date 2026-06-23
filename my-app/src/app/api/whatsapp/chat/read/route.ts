import { NextRequest, NextResponse } from "next/server";

import { markMessagesAsRead } from "@/modules/whatsapp/whatsapp.service";

export const dynamic = "force-dynamic";

export async function POST(req: NextRequest) {
  try {
    const { waId } = await req.json();

    if (!waId || typeof waId !== "string") {
      return NextResponse.json(
        {
          success: false,
          message: "waId is required",
        },
        {
          status: 400,
        },
      );
    }

    await markMessagesAsRead(waId);

    return NextResponse.json({
      success: true,
    });
  } catch (error) {
    console.warn("[whatsapp:read] fallback route failed", {
      error,
    });

    return NextResponse.json(
      {
        success: false,
        message: "Failed to mark chat as read",
      },
      {
        status: 500,
      },
    );
  }
}
