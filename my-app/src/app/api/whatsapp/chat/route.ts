import { NextRequest, NextResponse } from "next/server";

import { getChatController } from "@/modules/whatsapp/whatsapp.controller";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  try {
    const waId = req.nextUrl.searchParams.get("waId");

    if (!waId) {
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

    const chat = await getChatController(waId);

    if (!chat) {
      return NextResponse.json(
        {
          success: false,
          message: "Conversation not found",
        },
        {
          status: 404,
        },
      );
    }

    return NextResponse.json(
      {
        success: true,
        data: chat,
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    );
  } catch (error) {
    console.warn("[whatsapp:chat] fallback route failed", {
      error,
    });

    return NextResponse.json(
      {
        success: false,
        message: "Failed to fetch chat",
      },
      {
        status: 500,
      },
    );
  }
}
