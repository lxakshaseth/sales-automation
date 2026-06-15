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

    lastMessageAt: {
      type: Date,
    },
  },
  { timestamps: true },
);

export default mongoose.models.Contact ||
  mongoose.model("Contact", ContactSchema);
