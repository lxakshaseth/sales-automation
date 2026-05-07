import nodemailer from "nodemailer";

const transporter = nodemailer.createTransport({
  service: "gmail",

  auth: {
    user: process.env.SMTP_EMAIL,
    pass: process.env.SMTP_PASSWORD,
  },
});

interface SendEmailProps {
  to: string;
  subject: string;
  body: string;
}

export const sendEmailService = async ({
  to,
  subject,
  body,
}: SendEmailProps) => {
  const info = await transporter.sendMail({
    from: process.env.SMTP_EMAIL,
    to,
    subject,
    html: body,
  });

  return info;
};
