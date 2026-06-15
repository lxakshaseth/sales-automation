import { NextRequest, NextResponse } from "next/server";
import connectDB from "@/lib/db";
import Contact from "@/modules/whatsapp/contact.model";
import { saveOutboundMessage } from "@/modules/whatsapp/whatsapp.service";

export async function POST(req: NextRequest) {
  try {
    const { to, message } = await req.json();

    const response = await fetch(
      `https://graph.facebook.com/v25.0/${process.env.WHATSAPP_PHONE_NUMBER_ID}/messages`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.WHATSAPP_ACCESS_TOKEN}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messaging_product: "whatsapp",
          recipient_type: "individual",
          to,
          type: "text",
          text: { body: message },
        }),
      },
    );

    const data = await response.json();

    if (response.ok) {
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

      await saveOutboundMessage({
        contactId: contact._id,
        waMessageId: data?.messages?.[0]?.id,
        message,
        rawPayload: data,
      });
    }

    return NextResponse.json({
      success: response.ok,
      data,
    });
  } catch {
    return NextResponse.json(
      { success: false, message: "Failed to send message" },
      { status: 500 },
    );
  }
}
