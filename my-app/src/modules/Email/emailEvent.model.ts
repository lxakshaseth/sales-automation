import mongoose from "mongoose";

const EmailEventSchema = new mongoose.Schema(
  {
    emailId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Email",
      required: true,
    },

    type: {
      type: String,
      enum: ["CLICK", "UNSUBSCRIBE"],
      required: true,
    },

    metadata: {
      type: Object,
      default: {},
    },
  },
  {
    timestamps: true,
  },
);

export default mongoose.models.EmailEvent ||
  mongoose.model("EmailEvent", EmailEventSchema);
