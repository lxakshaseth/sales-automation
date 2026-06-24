import mongoose from "mongoose";

const ContactSchema = new mongoose.Schema(
  {
    waId: {
      type: String,
      required: true,
      unique: true,
    },

    name: {
      type: String,
    },

    customName: {
      type: String,
    },

    phone: {
      type: String,
    },

    aiEnabled: {
      type: Boolean,
      default: false,
    },

    conversationStatus: {
      type: String,
      enum: ["OPEN", "CLOSED"],
      default: "OPEN",
    },

    lifecycleRunId: {
      type: String,
    },

    lastInboundAt: {
      type: Date,
    },

    reminderSentAt: {
      type: Date,
    },

    closedAt: {
      type: Date,
    },

    summarySentAt: {
      type: Date,
    },

    lastMessageAt: {
      type: Date,
    },
  },
  { timestamps: true },
);

export default mongoose.models.Contact ||
  mongoose.model("Contact", ContactSchema);
