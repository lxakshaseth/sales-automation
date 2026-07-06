type ClosingIntentResult = {
  shouldClose: boolean;
  reason?: string;
};

const NEGATION_PATTERNS = [
  /\bdo\s+not\s+(?:stop|close|end|cancel)\b/,
  /\bdon['’]?t\s+(?:stop|close|end|cancel)\b/,
  /\bnever\s+(?:stop|close|end|cancel)\b/,
  /\bplease\s+(?:do\s+not|don['’]?t)\s+(?:stop|close|end|cancel)\b/,
  /\bkeep\s+(?:helping|going|chatting|talking)\b/,
  /\bcontinue\s+(?:helping|chatting|talking|the\s+chat|this\s+chat)\b/,
  /\bnot\s+(?:done|finished|over)\b/,
];

const QUESTION_CONTEXT_PATTERNS = [
  /\bhow\s+(?:do|can|to)\s+i\s+(?:stop|cancel|end|close)\b/,
  /\bcan\s+i\s+(?:stop|cancel|end|close)\b/,
  /\bwhat\s+happens\s+if\s+i\s+(?:stop|cancel|end|close)\b/,
];

const STRONG_CLOSE_PATTERNS = [
  /\b(?:can|could|would|will)\s+you\s+(?:please\s+)?(?:end|close|stop|cancel)\s+(?:the\s+)?(?:chat|conversation)\b/,
  /\b(?:end|close)\s+(?:the\s+)?(?:chat|conversation)\b/,
  /\b(?:stop|cancel)\s+(?:the\s+)?(?:chat|conversation)\b/,
  /\b(?:stop|cancel)\s+(?:this\s+)?(?:chat|conversation)\b/,
  /\b(?:please\s+)?(?:end|close)\s+(?:this\s+)?(?:chat|conversation)\b/,
  /\b(?:i(?:'| a)?m\s+)?(?:done|finished)\s+(?:here|for\s+now|with\s+this|with\s+the\s+chat)\b/,
  /\b(?:we(?:'| a)?re|we\s+are)\s+(?:done|finished)\b/,
  /\bthat(?:'s| is)\s+(?:all|it)\b.*\b(?:bye|goodbye|thanks|thank\s+you)\b/,
];

const SHORT_CLOSE_PATTERNS = [
  /^(?:bye|goodbye|good\s*bye|see\s+you|see\s+ya|cya|take\s+care|farewell)$/,
  /^(?:stop|cancel|done|finished|end|close)$/,
  /^(?:thanks|thank\s+you|thx|ty)[,.!\s]*(?:bye|goodbye|see\s+you|that(?:'s| is)\s+all)?$/,
  /^(?:ok|okay|alright|cool)[,.!\s]*(?:bye|done|thanks|thank\s+you|that(?:'s| is)\s+all)$/,
];

const FAREWELL_WORD_PATTERN =
  /\b(?:bye|goodbye|good\s*bye|see\s+you|see\s+ya|cya|take\s+care|farewell)\b/;
const THANKS_PATTERN = /\b(?:thanks|thank\s+you|thx|ty)\b/;
const COMPLETION_PATTERN = /\b(?:done|finished|that(?:'s| is)\s+(?:all|it))\b/;

export function detectConversationClosingIntent(
  message: string | undefined,
): ClosingIntentResult {
  const normalizedMessage = normalizeMessage(message);

  if (!normalizedMessage) {
    return {
      shouldClose: false,
    };
  }

  if (hasContextThatKeepsChatOpen(normalizedMessage)) {
    return {
      shouldClose: false,
      reason: "negated-or-informational-close-language",
    };
  }

  const strongMatch = STRONG_CLOSE_PATTERNS.find((pattern) =>
    pattern.test(normalizedMessage),
  );

  if (strongMatch) {
    return {
      shouldClose: true,
      reason: `strong-close:${strongMatch.source}`,
    };
  }

  const shortMatch = SHORT_CLOSE_PATTERNS.find((pattern) =>
    pattern.test(normalizedMessage),
  );

  if (shortMatch) {
    return {
      shouldClose: true,
      reason: `short-close:${shortMatch.source}`,
    };
  }

  if (
    FAREWELL_WORD_PATTERN.test(normalizedMessage) &&
    (THANKS_PATTERN.test(normalizedMessage) ||
      COMPLETION_PATTERN.test(normalizedMessage) ||
      normalizedMessage.length <= 40)
  ) {
    return {
      shouldClose: true,
      reason: "farewell-with-brief-close-context",
    };
  }

  return {
    shouldClose: false,
  };
}

function normalizeMessage(message: string | undefined) {
  return (message || "")
    .toLowerCase()
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    .replace(/[\u200B-\u200D\uFEFF]/g, "")
    .replace(/[^a-z0-9'?.!,\s-]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^[?.!,\s]+|[?.!,\s]+$/g, "");
}

function hasContextThatKeepsChatOpen(message: string) {
  return (
    NEGATION_PATTERNS.some((pattern) => pattern.test(message)) ||
    QUESTION_CONTEXT_PATTERNS.some((pattern) => pattern.test(message))
  );
}
