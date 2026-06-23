export type GroqChatMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

type GroqCompletionInput = {
  messages: GroqChatMessage[];
  maxTokens?: number;
  temperature?: number;
};

const GROQ_CHAT_COMPLETIONS_URL =
  "https://api.groq.com/openai/v1/chat/completions";

const DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile";

export class GroqServiceError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GroqServiceError";
  }
}

export async function createGroqChatCompletion({
  messages,
  maxTokens = 180,
  temperature = 0.4,
}: GroqCompletionInput) {
  const apiKey = process.env.GROQ_API_KEY;

  if (!apiKey) {
    throw new GroqServiceError("GROQ_API_KEY is not configured");
  }

  const response = await fetch(GROQ_CHAT_COMPLETIONS_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: process.env.GROQ_MODEL || DEFAULT_GROQ_MODEL,
      messages,
      temperature,
      max_tokens: maxTokens,
    }),
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");

    throw new GroqServiceError(
      `Groq request failed with status ${response.status}: ${body}`,
    );
  }

  const data = await response.json();
  const reply = data?.choices?.[0]?.message?.content?.trim();

  if (!reply) {
    throw new GroqServiceError("Groq response did not include reply text");
  }

  return reply;
}
