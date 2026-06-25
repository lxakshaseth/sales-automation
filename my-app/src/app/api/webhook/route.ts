import { NextRequest, NextResponse } from "next/server";
import {
  handleIncomingMessage,
  handleStatusUpdate,
} from "@/modules/whatsapp/whatsapp.controller";

export async function GET(req: NextRequest) {

  const searchParams = req.nextUrl.searchParams;
  const mode = searchParams.get("hub.mode");
  const token = searchParams.get("hub.verify_token");
  const challenge = searchParams.get("hub.challenge");

  if (mode === "subscribe" && token === process.env.WHATSAPP_VERIFY_TOKEN) {
    return new NextResponse(challenge, { status: 200 });
  }

  return NextResponse.json({ success: false }, { status: 403 });
}

export async function POST(req: NextRequest) {

  const body = await req.json();

  await handleIncomingMessage(body);
  await handleStatusUpdate(body);
  
  return NextResponse.json({ success: true });
}
