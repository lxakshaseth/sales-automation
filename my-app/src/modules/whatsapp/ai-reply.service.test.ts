import assert from "node:assert/strict";
import test from "node:test";

import {
  detectGreetingResponse,
  enforceSalesScopeResponse,
  generateSalesReply,
  OUT_OF_SCOPE_REPLY,
} from "./ai-reply.service";

test("returns the fixed redirect for an out-of-scope classification", () => {
  assert.equal(enforceSalesScopeResponse("OUT_OF_SCOPE"), OUT_OF_SCOPE_REPLY);
  assert.equal(
    enforceSalesScopeResponse("OUT_OF_SCOPE: Let us discuss movies."),
    OUT_OF_SCOPE_REPLY,
  );
});

test("returns only the customer-facing part of an in-scope response", () => {
  assert.equal(
    enforceSalesScopeResponse(
      "IN_SCOPE: I can help you choose the right CRM plan.",
    ),
    "I can help you choose the right CRM plan.",
  );
});

test("fails closed when the model returns an invalid response", () => {
  assert.equal(
    enforceSalesScopeResponse("Absolutely, let us talk about movies."),
    OUT_OF_SCOPE_REPLY,
  );
  assert.equal(enforceSalesScopeResponse(""), OUT_OF_SCOPE_REPLY);
});

test("returns a friendly reply for basic greeting-only messages", async () => {
  assert.equal(
    await generateSalesReply({
      message: "HI",
      waId: "919999999999",
    }),
    "Hello! How can I help you today?",
  );

  assert.equal(
    detectGreetingResponse("Hello", new Date("2026-07-06T06:00:00.000Z"), "UTC")
      ?.reply,
    "Hi! How may I assist you?",
  );

  assert.equal(
    detectGreetingResponse("hii", new Date("2026-07-06T06:00:00.000Z"), "UTC")
      ?.reply,
    "Hello! How can I help you today?",
  );
});

test("detects greeting prefix and leaves the rest for normal AI flow", () => {
  const greeting = detectGreetingResponse(
    "Hi, I need help choosing a plan",
    new Date("2026-07-06T06:00:00.000Z"),
    "UTC",
  );

  assert.equal(greeting?.reply, "Hello! How can I help you today?");
  assert.equal(greeting?.remainingMessage, "I need help choosing a plan");
  assert.equal(greeting?.isGreetingOnly, false);
});

test("uses current time for time-based greetings", () => {
  assert.equal(
    detectGreetingResponse(
      "Good morning",
      new Date("2026-07-06T06:00:00.000Z"),
      "UTC",
    )?.reply,
    "Good morning! How can I help you today?",
  );

  assert.equal(
    detectGreetingResponse(
      "good afternoon",
      new Date("2026-07-06T13:00:00.000Z"),
      "UTC",
    )?.reply,
    "Good afternoon! How may I assist you?",
  );

  assert.equal(
    detectGreetingResponse(
      "GOOD EVENING",
      new Date("2026-07-06T18:00:00.000Z"),
      "UTC",
    )?.reply,
    "Good evening! How can I help you?",
  );

  assert.equal(
    detectGreetingResponse(
      "Good night",
      new Date("2026-07-06T22:00:00.000Z"),
      "UTC",
    )?.reply,
    "Good night! Have a great rest.",
  );
});
