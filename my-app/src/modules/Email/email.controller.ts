import Email from "./email.model";
import { sendEmailService } from "./email.service";

interface EmailBody {
  to: string;
  subject: string;
  body: string;
}

export const sendEmail = async ({ to, subject, body }: EmailBody) => {
  try {
    await sendEmailService({
      to,
      subject,
      body,
    });

    const savedEmail = await Email.create({
      to,
      subject,
      body,
      status: "SENT",
    });

    return savedEmail;
  } catch {
    const failedEmail = await Email.create({
      to,
      subject,
      body,
      status: "FAILED",
    });

    return failedEmail;
  }
};
