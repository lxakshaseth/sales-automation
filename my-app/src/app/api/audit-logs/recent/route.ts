import connectDB from "@/lib/db";
import { NextResponse } from "next/server";
import AuditLog from "@/modules/audit-log/auditLog.model";
import { getRecentAuditLogs } from "@/modules/audit-log/auditLog.controller";

export async function GET() {
  await connectDB();

  return getRecentAuditLogs();
}

export async function DELETE(req: Request) {
  await connectDB();

  try {
    const { fromDate, toDate } = await req.json();

    const startDate = new Date(fromDate);

    const endDate = new Date(toDate);
    endDate.setHours(23, 59, 59, 999);

    const result = await AuditLog.deleteMany({
      createdAt: {
        $gte: startDate,
        $lte: endDate,
      },
    });

    return NextResponse.json({
      success: true,
      deletedCount: result.deletedCount,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        success: false,
        message: error.message,
      },
      { status: 500 },
    );
  }
}
