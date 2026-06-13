import mongoose from "mongoose";

const MessageSchema = new mongoose.Schema(
  {
    contactId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Contact",
      required: true,
    },

    waMessageId: {
      type: String,
      index: true,
    },

    direction: {
      type: String,
      enum: ["INBOUND", "OUTBOUND"],
      required: true,
    },

    type: {
      type: String,
      enum: ["text", "template"],
      default: "text",
    },

    message: String,

    status: {
      type: String,
      enum: ["SENT", "DELIVERED", "READ", "FAILED"],
      default: "SENT",
    },

    rawPayload: Object,
  },
  { timestamps: true },
);

export default mongoose.models.Message ||
  mongoose.model("Message", MessageSchema);
