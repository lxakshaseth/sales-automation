import AuditLog from "./auditLog.model";

export async function createAuditLog(
  module: string,
  action: string,
  item: string,
  details: string
) {
  try {
    await AuditLog.create({
      module,
      action,
      item,
      details,
    });
  } catch (error) {
    console.error("Audit Log Error:", error);
  }
}