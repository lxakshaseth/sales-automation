import { NextRequest, NextResponse } from "next/server";
import bycrypt from "bcryptjs";
import User from "./user.model";
import { generateToken } from "./generateToken";

export const registerController = async (req: NextRequest) => {
  try {
    const body = await req.json();
    const { name, email, mobile, password } = body;

    const userExists = await User.findOne({ email });
    if (userExists) {
      return NextResponse.json({ success: false, message: "User already exists" },{ status: 400 },
      );
    }
    if (!/^[0-9]{10}$/.test(mobile)) {
      return NextResponse.json({ success: false, message: "Invalid mobile number" },{ status: 400 });
    }

    const hashedPassword = await bycrypt.hash(password, 10);
    await User.create({ name, email, mobile, password: hashedPassword });
    // const token = generateToken(user._id.toString());

    return NextResponse.json(
      { success: true,  message: "Registration successful", },
      { status: 201 },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};
export const loginController = async (req: NextRequest) => {
  try {
    const body = await req.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { success: false, message: "Email and password are required" },
        { status: 400 },
      );
    }
    const user = await User.findOne({ email });
    if (!user) {
      return NextResponse.json(
        { success: false, message: "invalid email and password" },
        { status: 401 },
      );
    }
    const isMatch = await bycrypt.compare(password, user.password);
    if (!isMatch) {
      return NextResponse.json(
        { success: false, message: "Invalid email or password" },
        { status: 401 },
      );
    }

    const token = generateToken(user._id.toString());
    return NextResponse.json(
      { success: true, token, data: user },
      { status: 200 },
    );
  } catch (error: any) {
    return NextResponse.json(
      { success: false, message: error.message },
      { status: 500 },
    );
  }
};
