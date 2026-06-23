import { NextResponse } from "next/server";

import { markMessagesAsRead } from "@/modules/whatsapp/whatsapp.service"; // Import the function to mark messages as read from the WhatsApp service modulecide 

export const dynamic = "force-dynamic";

export async function POST(
  _req: Request,
  {
    params,
  }: {
    params:
      | Promise<{
          waId: string;
        }>
      | {
          waId: string;
        };
  },
) {
  try {
    const { waId } = await params;

    await markMessagesAsRead(waId);

    return NextResponse.json({
      success: true,
    });
  } catch (error) {
    console.error("[whatsapp:read] route failed", {
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
