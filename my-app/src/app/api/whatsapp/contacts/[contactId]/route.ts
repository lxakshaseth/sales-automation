import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  updateContactAiEnabledController,
  updateContactNameController,
} from "@/modules/whatsapp/whatsapp.controller";

export const dynamic = "force-dynamic";

export async function PATCH(
  req: NextRequest,
  {
    params,
  }: {
    params: Promise<{
      contactId: string;
    }>;
  },
) {
  try {
    const { contactId } =
      await params;

    const { aiEnabled, customName } =
      await req.json();

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
    console.warn("[whatsapp:contacts] route update failed", {
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
