import { NextResponse } from "next/server";
import AuditLog from "./auditLog.model";

export async function getRecentAuditLogs() {
  try {
     const logs = await AuditLog.find()
  .sort({ createdAt: -1 });

    return NextResponse.json({
      success: true,
      data: logs,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        success: false,
        message: error.message,
      },
      { status: 500 }
    );
  }
}