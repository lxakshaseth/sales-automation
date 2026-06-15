import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
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

    const { customName } =
      await req.json();

    const contact =
      await updateContactNameController(
        contactId,
        customName,
      );

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