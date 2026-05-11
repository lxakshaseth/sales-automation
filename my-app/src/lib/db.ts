import mongoose from "mongoose";

const MONGODB_URI = process.env.MONGODB_URI;

if (!MONGODB_URI) {
  throw new Error("MONGODB_URI is missing");
}

export const connectDB = async () => {
  try {
    if (mongoose.connection.readyState === 1) {
      return;
    }

    await mongoose.connect(MONGODB_URI);

    console.log("✅ MongoDB Connected");
  } catch (error) {
    console.log("MongoDB Error:", error);

    process.exit(1);
  }
};