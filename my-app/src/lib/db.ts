import mongoose from "mongoose";

const connectDB = async () => {
  try {
    const dbName = process.env.MONGODB_DB_NAME || "sales-automation";

    if (
      mongoose.connection.readyState === 1 &&
      mongoose.connection.name === dbName
    ) {
      return;
    }

    if (mongoose.connection.readyState !== 0) {
      await mongoose.disconnect();
    }

    const MONGODB_URI = process.env.MONGODB_URI;

    if (!MONGODB_URI) {
      throw new Error("MONGODB_URI is missing");
    }

    await mongoose.connect(MONGODB_URI, {
      dbName,
    });

    console.log("MongoDB Connected");
  } catch (error) {
    console.log("MongoDB Connection Failed", error);

    throw error;
  }
};

export default connectDB;
