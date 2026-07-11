import Email from "./email.model";
import { sendEmailService } from "./email.service"; // Importing the sendEmailService function from the email service module to handle sending emails
import type { EmailAttachment } from "./email.service";
import Unsubscribed from "./unsubscribed.model";
import { injectTrackingLinks } from "./email.util";
import Template from "./template.model";
import { renderTemplate } from "./email.util";
import Lead from "@/modules/leads/leads.model";

import { createUnsubscribeLink } from "./email.util";

interface EmailBody {
  to: string;
  subject?: string;
  body?: string;

  templateName?: string;

  variables?: {
    [key: string]: string;
  };

  emailId?: string;
  leadId?: string;
  attachments?: EmailAttachment[];
  followUpStage?: number;
}

export const sendEmail = async ({
  to,
  subject,
  body,
  templateName,
  variables = {},
  attachments = [],
  leadId,
  followUpStage,
}: EmailBody) => {
  try {
    // 1. Check unsubscribe list
    const unsubscribedUser = await Unsubscribed.findOne({
      email: to,
    });

    if (unsubscribedUser) {
      console.log(`${to} has unsubscribed. Skipping email.`);

      await Email.create({
        to,
        subject: subject || "UNSUBSCRIBED",
        body: body || "",
        status: "SKIPPED",
      });

      return null;
    }

    // 2. Prepare subject + body
    let finalSubject = subject || "";
    let finalBody = body || "";

    // Render variables for direct subject/body too
    finalSubject = renderTemplate(finalSubject, variables);

    finalBody = renderTemplate(finalBody, variables);

    // 3. Render template if provided
    if (templateName) {
      const template = await Template.findOne({
        name: templateName,
      });

      if (!template) {
        throw new Error("Template not found");
      }

      finalSubject = renderTemplate(template.subject, variables);

      finalBody = renderTemplate(template.body, variables);
    }

    // 4. Save email
    const savedEmail = await Email.create({
      to,
      subject: finalSubject,
      body: finalBody,
      status: "PENDING",
    });

    const BASE_URL = process.env.BASE_URL;

    // 5. Inject click tracking links
    const trackedBody = injectTrackingLinks({
      html: finalBody,
      baseUrl: BASE_URL!,
      emailId: savedEmail._id.toString(),
    });

    // 6. Create unsubscribe link
    const unsubscribeUrl = createUnsubscribeLink({
      baseUrl: BASE_URL!,
      email: to,
      emailId: savedEmail._id.toString(),
    });

    const unsubscribeLink = `
      <br /><br />
      <a href="${unsubscribeUrl}">
        Unsubscribe
      </a>
    `;

    // 7. Final email body
    const completeBody = trackedBody + unsubscribeLink;

    // 8. Send email
    await sendEmailService({
      to,
      subject: finalSubject,
      body: completeBody,
      attachments,
    });

    // 9. Update status
    savedEmail.status = "SENT";
    await savedEmail.save();

    if (leadId) {
      await Lead.findByIdAndUpdate(leadId, {
        $set: {
          lastEmailSentAt: new Date(),
          status: "contacted",
          stageEnteredAt: new Date(),
          lastActivity: `Email sent: ${finalSubject}`,
        },
        ...(followUpStage !== undefined && { $max: { followUpStage } }),
      });
    }

    return savedEmail;
  } catch (error) {
    console.log("EMAIL ERROR:", error);

    const failedEmail = await Email.create({
      to,
      subject: subject || "FAILED_EMAIL",
      body: body || "FAILED_EMAIL_BODY",
      status: "FAILED",
    });

    return failedEmail;
  }
};
