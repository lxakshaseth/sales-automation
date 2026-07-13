export async function readJsonResponse<T>(
  response: Response,
): Promise<T | null> {
  const contentType = response.headers.get("content-type") || "";

  if (!contentType.includes("application/json")) {
    return null;
  }

  try {
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

type ApiMessage = {
  message?: string;
};

function getFallbackResponseMessage(response: Response, fallbackMessage: string) {
  if (response.status === 404) {
    return "The API endpoint was not found. Restart the dev server and try again.";
  }

  if (response.status >= 500) {
    return "Server error. Please try again in a moment.";
  }

  return fallbackMessage;
}

export async function readApiResponse<T extends ApiMessage = ApiMessage>(
  response: Response,
  fallbackMessage: string,
): Promise<T & ApiMessage> {
  const json = await readJsonResponse<T & ApiMessage>(response);

  if (json) {
    return json;
  }

  return {
    message: getFallbackResponseMessage(response, fallbackMessage),
  } as T & ApiMessage;
}
