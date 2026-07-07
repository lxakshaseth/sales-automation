import mongoose, { Schema } from "mongoose";

const leadSchema = new Schema(
  {
    firstName: {
      type: String,
      required: true,
      trim: true,
    },

    lastName: {
      type: String,
      trim: true,
    },

    email: {
      type: String,
      required: true,
      lowercase: true,
      trim: true,
    },

    phone: {
      type: String,
      required: true,
      trim: true,
    },

    company: {
      type: String,
      trim: true,
    },

    country: {
      type: String,
    },

    state: {
      type: String,
    },

    timezone: {
      type: String,
    },

    source: {
      type: String,
      enum: ["manual", "csv", "website", "facebook", "linkedin"],
      default: "manual",
    },

    status: {
      type: String,
      enum: [
        "new",
        "contacted",
        "interested",
        "follow_up",
        "not_interested",
        "converted",
      ],
      default: "new",
    },

    stageEnteredAt: {
      type: Date,
      default: Date.now,
    },

    lastActivity: {
      type: String,
      default: "Lead Created",
    },

    score: {
      type: Number,
      default: 0,
    },

    tags: {
      type: [String],
      default: [],
    },

    lastContactedAt: {
      type: Date,
    },

    lastEmailSentAt: {
      type: Date,
      default: null,
    },

    nextFollowUpAt: {
      type: Date,
    },

    campaign: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Campaign",
      default: null,
    },
  },
  {
    timestamps: true,
  },
);

const Lead = mongoose.models.Lead || mongoose.model("Lead", leadSchema);

export default Lead;
