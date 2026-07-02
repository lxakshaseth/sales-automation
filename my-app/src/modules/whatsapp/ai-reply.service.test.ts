import assert from "node:assert/strict";
import test from "node:test";

import {
  enforceSalesScopeResponse,
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
