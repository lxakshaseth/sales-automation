interface TemplateVariables {
  [key: string]: string;
}

export const renderTemplate = (
  template: string,
  variables: TemplateVariables,
) => {
  let renderedTemplate = template;

  Object.keys(variables).forEach((key) => {
    const regex = new RegExp(`{{${key}}}`, "g");

    renderedTemplate = renderedTemplate.replace(
      regex,
      variables[key],
    );
  });

  return renderedTemplate;
};

export const injectTrackingLinks = ({
  html,
  baseUrl,
  emailId,
}: {
  html: string;
  baseUrl: string;
  emailId: string;
}) => {
  return html.replace(
    /<a\s+(?:[^>]*?\s+)?href=["']([^"']*)["']/g,
    (_, originalUrl) => {
      const trackedUrl =
        `${baseUrl}/api/email/click?url=${encodeURIComponent(originalUrl)}&emailId=${emailId}`;

      return `<a href="${trackedUrl}"`;
    },
  );
};

export const createUnsubscribeLink = ({
  baseUrl,
  email,
  emailId,
}: {
  baseUrl: string;
  email: string;
  emailId: string;
}) => {
  const encodedEmail = encodeURIComponent(email);

  return `${baseUrl}/api/email/unsubscribe?email=${encodedEmail}&emailId=${emailId}`;
};