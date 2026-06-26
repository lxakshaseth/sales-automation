import { NextRequest, NextResponse } from "next/server";
import { getContactsController } from "@/modules/whatsapp/whatsapp.controller";

interface ContactDoc {
  createdAt: string | Date;
}

export async function GET(req: NextRequest) {
  try {
    const contacts = (await getContactsController()) as ContactDoc[];

    const now = new Date();

    const startOfThisWeek = new Date(now);
    const day = startOfThisWeek.getDay();
    const diff = day === 0 ? 6 : day - 1;
    startOfThisWeek.setDate(now.getDate() - diff);
    startOfThisWeek.setHours(0, 0, 0, 0);

    const startOfLastWeek = new Date(startOfThisWeek);
    startOfLastWeek.setDate(startOfThisWeek.getDate() - 7);

    const endOfLastWeek = new Date(startOfThisWeek);

    let newCount = 0;
    let contactedCount = 0;

    for (const contact of contacts) {
      const createdAt = new Date(contact.createdAt);

      if (createdAt >= startOfThisWeek && createdAt <= now) {
        newCount++;
      } else if (createdAt >= startOfLastWeek && createdAt < endOfLastWeek) {
        contactedCount++;
      }
    }

    return NextResponse.json({
      data: [
        { status: "new", count: newCount },
        { status: "contacted", count: contactedCount },
      ],
      date_range: {
        from: startOfLastWeek.toISOString().split("T")[0],
        to: now.toISOString().split("T")[0],
      },
    });
  } catch (error) {
    return NextResponse.json({ error: "Failed to load funnel data" }, { status: 503 });
  }
}