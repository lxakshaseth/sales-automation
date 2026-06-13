import jwt from "jsonwebtoken";

export const generateToken = (id: string) => {
  return jwt.sign({ id }, process.env.jwt_secret as string, {
    expiresIn: "7d",
  });
};
