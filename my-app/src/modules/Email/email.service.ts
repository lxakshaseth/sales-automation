import nodemailer from "nodemailer";

export interface EmailAttachment {
  filename: string;
  content: Buffer | string;
  contentType?: string;
}

interface SendEmailProps {  // Defining an interface for the properties required to send an email
  to: string;
  subject: string;
  body: string;
  attachments?: EmailAttachment[];
}

export const sendEmailService = async ({
  to,
  subject,
  body,
  attachments = [],
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
    attachments,
  });
  return info;
};
