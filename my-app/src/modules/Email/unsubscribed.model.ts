import mongoose from "mongoose";

const UnsubscribedSchema = new mongoose.Schema(
  {
    email: {
      type: String,
      required: true,
      unique: true,
    },
  },
  {
    timestamps: true,
  },
);

export default mongoose.models.Unsubscribed ||
  mongoose.model("Unsubscribed", UnsubscribedSchema);
