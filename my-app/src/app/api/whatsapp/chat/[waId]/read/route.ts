import { NextResponse } from "next/server";

import { markMessagesAsRead } from "@/modules/whatsapp/whatsapp.service";

export async function POST(
  req: Request,
  {
    params,
  }: {
    params: Promise<{
      waId: string;
    }>;
  },
) {
  try {
    const { waId } = await params;

    await markMessagesAsRead(waId);

    return NextResponse.json({
      success: true,
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
