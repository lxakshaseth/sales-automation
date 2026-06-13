import { NextRequest, NextResponse } from "next/server";

import {
  getChatController,
} from "@/modules/whatsapp/whatsapp.controller";

export async function GET(
  req: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      waId: string;
    }>;
  },
) {
  try {
    const { waId } =
      await params;

    const chat =
      await getChatController(
        waId,
      );

    return NextResponse.json({
      success: true,
      data: chat,
    });
  } catch {
    return NextResponse.json(
      {
        success: false,
      },
      {
        status: 500,
      },
    );
  }
}