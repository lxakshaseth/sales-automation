import assert from "node:assert/strict";
import test from "node:test";

import { detectConversationClosingIntent } from "./conversation-closing-intent.service";

test("detects farewell closing intent", () => {
  for (const message of [
    "bye",
    "goodbye",
    "see you",
    "thanks, bye",
    "THANK YOU, GOODBYE!",
  ]) {
    assert.equal(
      detectConversationClosingIntent(message).shouldClose,
      true,
      message,
    );
  }
});

test("detects command closing intent", () => {
  for (const message of [
    "stop",
    "cancel",
    "end chat",
    "close chat",
    "please close the conversation",
    "can you close the chat?",
    "done",
    "DONE!",
    "Stop.",
  ]) {
    assert.equal(
      detectConversationClosingIntent(message).shouldClose,
      true,
      message,
    );
  }
});

test("does not close for negated or informational phrases", () => {
  for (const message of [
    "don't stop helping me",
    "please do not close the conversation",
    "how do I stop this notification?",
    "I am done comparing options, what are the next steps?",
    "Can you tell me when this offer ends?",
  ]) {
    assert.equal(
      detectConversationClosingIntent(message).shouldClose,
      false,
      message,
    );
  }
});
