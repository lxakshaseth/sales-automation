import mongoose from "mongoose";

const TemplateSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
      unique: true,
    },

    subject: {
      type: String,
      required: true,
    },

    body: {
      type: String,
      required: true,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.models.Template ||
  mongoose.model("Template", TemplateSchema);