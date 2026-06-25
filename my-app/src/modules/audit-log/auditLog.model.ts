import mongoose from "mongoose";

const AuditLogSchema = new mongoose.Schema(
  {
    module: {
      type: String,
      required: true,
    },
    action: {
      type: String,
      required: true,
    },
    item: {
      type: String,
      required: true,
    },
    details: {
      type: String,
      required: true,
    },
  },
  {
    timestamps: true,
  }
);

const AuditLog =
  mongoose.models.AuditLog ||
  mongoose.model("AuditLog", AuditLogSchema);

export default AuditLog;