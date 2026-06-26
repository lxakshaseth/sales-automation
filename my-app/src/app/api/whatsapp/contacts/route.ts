import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  getContactsController,    //get
  updateContactAiEnabledController,
  updateContactNameController,
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

export async function PATCH(req: NextRequest) {
  try {
    const { aiEnabled, contactId, customName } = await req.json();

    if (!contactId || typeof contactId !== "string") {
      return NextResponse.json(
        {
          success: false,
          message: "contactId is required",
        },
        {
          status: 400,
        },
      );
    }

    let contact = null;

    if (typeof customName === "string") {
      contact = await updateContactNameController(
        contactId,
        customName,
      );
    }

    if (typeof aiEnabled === "boolean") {
      contact = await updateContactAiEnabledController(
        contactId,
        aiEnabled,
      );
    }

    if (!contact) {
      return NextResponse.json(
        {
          success: false,
          message: "Contact not found",
        },
        {
          status: 404,
        },
      );
    }

    return NextResponse.json({
      success: true,
      data: contact,
    });
  } catch (error) {
    console.warn("[whatsapp:contacts] fallback update failed", {
      error,
    });

    return NextResponse.json(
      {
        success: false,
        message: "Failed to update contact",
      },
      {
        status: 500,
      },
    );
  }
}
