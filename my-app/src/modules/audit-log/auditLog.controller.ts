import { NextResponse } from "next/server";
import AuditLog from "./auditLog.model";

export async function getRecentAuditLogs() {
  try {
    const sixMonthsAgo = new Date();
    sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);

    const deleted = await AuditLog.deleteMany({
      createdAt: {
        $lt: sixMonthsAgo,
      },
    });

    const logs = await AuditLog.find().sort({
      createdAt: -1,
    });

    return NextResponse.json({
      success: true,
      data: logs,
      autoDeleted: deleted.deletedCount > 0,
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
