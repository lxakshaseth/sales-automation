import mongoose from "mongoose";

const funnelStepSchema = new mongoose.Schema(
  {
    step: {
      type: String,
      enum: ["email", "sms", "ai_call", "human_call"],
      required: true,
    },

    action: {
      type: String,
      required: true,
    },

    waitHours: {
      type: Number,
      default: 0,
    },

    enabled: {
      type: Boolean,
      default: true,
    },
  },
  {
    _id: false,
  },
);

const templateSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
    },

    subject: {
      type: String,
      default: "",
    },

    body: {
      type: String,
      required: true,
    },
  },
  {
    _id: false,
  },
);

const retrySchema = new mongoose.Schema(
  {
    email: {
      type: Number,
      default: 2,
    },

    sms: {
      type: Number,
      default: 1,
    },

    call: {
      type: Number,
      default: 3,
    },
  },
  {
    _id: false,
  },
);

const scheduleSettingsSchema = new mongoose.Schema(
  {
    businessHoursOnly: {
      type: Boolean,
      default: true,
    },

    startHour: {
      type: Number,
      default: 9,
    },

    endHour: {
      type: Number,
      default: 18,
    },
  },
  {
    _id: false,
  },
);

const campaignSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
      trim: true,
    },

    description: {
      type: String,
      default: "",
    },

    status: {
      type: String,
      enum: ["draft", "active", "paused"],
      default: "draft",
    },

    timezoneStrategy: {
      type: String,
      enum: ["auto", "manual"],
      default: "auto",
    },

    funnel: {
      type: [funnelStepSchema],

      validate: {
        validator: function (v: any[]) {
          return v.length > 0;
        },

        message: "At least one funnel step is required",
      },
    },

    emailTemplates: {
      type: [templateSchema],
      default: [],
    },

    smsTemplates: {
      type: [templateSchema],
      default: [],
    },

    retryLimits: {
      type: retrySchema,
      default: () => ({}),
    },

    scheduleSettings: {
      type: scheduleSettingsSchema,
      default: () => ({}),
    },
  },
  {
    timestamps: true,
  },
);

const Campaign =
  mongoose.models.Campaign ||
  mongoose.model("Campaign", campaignSchema);

export default Campaign;