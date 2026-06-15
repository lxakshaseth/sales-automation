import mongoose from "mongoose";

const EmailSchema = new mongoose.Schema(
  {
    to: {
      type: String,
      required: true,
    },

    subject: {
      type: String,
      required: true,
    },

    body: {
      type: String,
      required: true,
    },

    status: {
      type: String,
      enum: ["PENDING", "SENT", "FAILED"],
      default: "PENDING",
    },
  },
  {
    timestamps: true,
  },
);

export default mongoose.models.Email || mongoose.model("Email", EmailSchema);
