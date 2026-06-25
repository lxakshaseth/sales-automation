import connectDB from "@/lib/db";
import { getRecentAuditLogs } from "@/modules/audit-log/auditLog.controller";

export async function GET() {
  await connectDB();

  return getRecentAuditLogs();
}