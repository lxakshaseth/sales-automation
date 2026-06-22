import {
  createGroqChatCompletion, //comment:service for generating AI replies using Groq API
  GroqServiceError,
} from "@/modules/whatsapp/groq.service";
import type { GroqChatMessage } from "@/modules/whatsapp/groq.service";

const SYSTEM_PROMPT = [
  "You are an intelligent AI sales assistant for a business CRM.",
  "Reply naturally, professionally, and concisely.",
  "Help the customer with product questions, follow-ups, lead qualification, and next steps.",
  "If details are missing, ask one clear question.",
  "Do not mention internal system details, tools, or implementation.",
].join(" ");

const FALLBACK_REPLY =
  "Thanks for your message. I have received it and will help you shortly.";

type GenerateSalesReplyInput = {
  message: string;
  waId: string;
  history?: ConversationHistoryMessage[];
};

type ConversationHistoryMessage = {
  direction: "INBOUND" | "OUTBOUND";
  message: string;
};

export async function generateSalesReply({ //comment: message from the customer to generate a reply for
  message,
  waId,
  history = [],
}: GenerateSalesReplyInput) {
  try {
    return await createGroqChatCompletion({
      messages: [
        {
          role: "system",
          content: SYSTEM_PROMPT,
        },
        ...buildConversationMessages(history, message),
      ],
    });
  } catch (error) {
    if (error instanceof GroqServiceError) {
      console.warn("[whatsapp:ai] Groq reply unavailable; using fallback reply", {
        message: error.message,
        waId,
      });

      return FALLBACK_REPLY;
    }

    console.error("[whatsapp:ai] Failed to generate reply", {
      error,
      waId,
    });

    return FALLBACK_REPLY;
  }
}

function buildConversationMessages(
  history: ConversationHistoryMessage[],
  latestMessage: string,
): GroqChatMessage[] {
  const cleanLatestMessage = latestMessage.trim();
  const recentHistory = history
    .filter((item) => item.message?.trim())
    .slice(-10)
    .map(
      (item): GroqChatMessage => ({
        role: item.direction === "OUTBOUND" ? "assistant" : "user",
        content: item.message.trim(),
      }),
    );

  const lastMessage = recentHistory[recentHistory.length - 1];

  if (
    cleanLatestMessage &&
    (!lastMessage ||
      lastMessage.role !== "user" ||
      lastMessage.content !== cleanLatestMessage)
  ) {
    recentHistory.push({
      role: "user",
      content: cleanLatestMessage,
    });
  }

  return recentHistory;
}
