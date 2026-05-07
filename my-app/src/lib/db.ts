import mongoose from "mongoose";
const MONGODB_URI = process.env.MONGODB_URI!;

const connectDB = async () => {
  try {
    if (mongoose.connection.readyState === 1) return;

    await mongoose.connect(MONGODB_URI);

    console.log("MongoDB Connected");
  } catch (error) {
    console.log("MongoDB Connection Failed", error);
  }
};

export default connectDB;