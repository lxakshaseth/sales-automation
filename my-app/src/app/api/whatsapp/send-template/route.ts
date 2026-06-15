import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {

    console.log("SEND TEMPLATE ROUTE HIT");
    
  try {
    const { to } = await req.json();

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
          to,
          type: "template",
          template: {
            name: "hello_world",
            language: {
              code: "en_US",
            },
          },
        }),
      },
    );

    const data = await response.json();

    return NextResponse.json({
      success: response.ok,
      data,
    });
  } catch (error) {
    console.error(error);

    return NextResponse.json(
      {
        success: false,
        message: "Failed to send WhatsApp template message",
      },
      {
        status: 500,
      },
    );
  }
}
