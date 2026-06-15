import { NextResponse } from "next/server";

import {
  getContactsController,
} from "@/modules/whatsapp/whatsapp.controller";

export async function GET() {
  try {
    const contacts =
      await getContactsController();

    return NextResponse.json({
      success: true,
      data: contacts,
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