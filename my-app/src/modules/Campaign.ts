import mongoose, { Schema, model, models } from "mongoose";

const CampaignSchema = new Schema(
  {
    name: { type: String, required: true, trim: true },
    slug: { type: String, required: true, unique: true, index: true },
    description: { type: String },
    regions: {
      type: [String],
      enum: ["USA", "India", "Dubai", "Europe"],
    },
    regionLogic: { type: Schema.Types.Mixed, default: {} },
    status: {
      type: String,
      enum: ["draft", "active", "paused", "stopped"],
      default: "draft",
    },
  },
  { timestamps: true, strict: false }
);

// Prevent model overwrite in Next.js (IMPORTANT)
export default models.Campaign || model("Campaign", CampaignSchema);