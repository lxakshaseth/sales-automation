import { NextRequest, NextResponse } from "next/server"; // Importing NextRequest and NextResponse from the Next.js server module to handle HTTP requests and responses
import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import {
  saveOutboundMessage,
  sendWhatsAppTextMessage,
} from "@/modules/whatsapp/whatsapp.service";

export async function POST(req: NextRequest) {
  try {
    const { to, message } = await req.json();

    const sendResult = await sendWhatsAppTextMessage({
      to,
      message,
    });
    let outboundMessage = null;

    if (sendResult.ok) {
      await connectDB();

      const contact = await Contact.findOneAndUpdate(
        { waId: to },
        {
          $setOnInsert: {
            waId: to,
            phone: to,
          },
          $set: {
            lastMessageAt: new Date(),
          },
        },
        {
          upsert: true,
          new: true,
        },
      );

      outboundMessage = await saveOutboundMessage({
        contactId: contact._id,
        waMessageId: sendResult.data?.messages?.[0]?.id,
        message,
        rawPayload: sendResult.data,
      });
    }

    return NextResponse.json(
      {
        success: sendResult.ok,
        data: {
          whatsapp: sendResult.data,
          outboundMessage,
        },
      },
      {
        status: sendResult.ok ? 200 : 502,
      },
    );
  } catch {
    return NextResponse.json(
      { success: false, message: "Failed to send message" },
      { status: 500 },
    );
  }
}
