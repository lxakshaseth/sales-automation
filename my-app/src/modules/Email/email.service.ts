import nodemailer from "nodemailer";

interface SendEmailProps {  // Defining an interface for the properties required to send an email
  to: string;
  subject: string;
  body: string;
}

export const sendEmailService = async ({
  to,
  subject,
  body,
}: SendEmailProps) => {

  const SMTP_EMAIL = process.env.SMTP_EMAIL;
  const SMTP_PASSWORD = process.env.SMTP_PASSWORD;

  if (!SMTP_EMAIL || !SMTP_PASSWORD) {
    throw new Error("SMTP credentials missing");
  }

  const transporter = nodemailer.createTransport({
    service: "gmail",

    auth: {
      user: SMTP_EMAIL,
      pass: SMTP_PASSWORD,
    },
  });

  const info = await transporter.sendMail({
    from: SMTP_EMAIL,
    to,
    subject,
    html: body,
  });

  return info;
};