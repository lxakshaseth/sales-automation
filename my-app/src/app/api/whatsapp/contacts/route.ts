import { NextResponse } from "next/server";

import {
  getContactsController,
} from "@/modules/whatsapp/whatsapp.controller";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const contacts =
      await getContactsController();

    return NextResponse.json({
      success: true,
      data: contacts,
    }, {
      headers: {
        "Cache-Control": "no-store",
      },
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
