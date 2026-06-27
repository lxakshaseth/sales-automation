import mongoose from "mongoose";

type MongooseCache = {
  conn: typeof mongoose | null;
  promise: Promise<typeof mongoose> | null;
  uri: string | null;
  dbName: string | null;
};

const globalWithMongoose = globalThis as typeof globalThis & {
  mongooseCache?: MongooseCache;
};

const cached =
  globalWithMongoose.mongooseCache ??
  (globalWithMongoose.mongooseCache = {
    conn: null,
    promise: null,
    uri: null,
    dbName: null,
  });

const connectDB = async () => {
  const MONGODB_URI = process.env.MONGODB_URI;
  const dbName = process.env.MONGODB_DB_NAME || "sales-automation";

  if (!MONGODB_URI) {
    throw new Error("MONGODB_URI is missing");
  }

  if (mongoose.connection.readyState === 1 && mongoose.connection.name === dbName) {
    cached.conn = mongoose;
    cached.uri = MONGODB_URI;
    cached.dbName = dbName;
    return cached.conn;
  }

  if (mongoose.connection.readyState === 0) {
    cached.conn = null;
    cached.promise = null;
  }

  if (!cached.promise || cached.uri !== MONGODB_URI || cached.dbName !== dbName) {
    cached.uri = MONGODB_URI;
    cached.dbName = dbName;
    cached.promise = mongoose
      .connect(MONGODB_URI, {
        dbName,
      })
      .then((mongooseInstance) => {
        console.log("MongoDB Connected");
        return mongooseInstance;
      });
  }

  try {
    cached.conn = await cached.promise;
    return cached.conn;
  } catch (error) {
    cached.promise = null;
    cached.conn = null;
    console.log("MongoDB Connection Failed", error);
    throw error;
  }
};

export default connectDB;
