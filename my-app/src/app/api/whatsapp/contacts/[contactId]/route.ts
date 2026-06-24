import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  updateContactAiEnabledController,
  updateContactNameController,
} from "@/modules/whatsapp/whatsapp.controller";

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

    return NextResponse.json({
      success: true,
      data: contact,
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
