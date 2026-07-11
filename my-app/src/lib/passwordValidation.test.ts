import assert from "node:assert/strict";
import test from "node:test";

import {
  PASSWORD_REQUIREMENTS,
  PASSWORD_VALIDATION_MESSAGE,
  getPasswordRequirementResults,
  getPasswordValidationError,
  isStrongPassword,
} from "./passwordValidation";

test("accepts passwords that satisfy the full policy", () => {
  assert.equal(isStrongPassword("ValidPass1!"), true);
  assert.equal(getPasswordValidationError("ValidPass1!"), null);
});

test("rejects passwords shorter than 8 characters", () => {
  assert.equal(isStrongPassword("Aa1!abc"), false);
});

test("rejects passwords without uppercase letters", () => {
  assert.equal(isStrongPassword("validpass1!"), false);
});

test("rejects passwords without lowercase letters", () => {
  assert.equal(isStrongPassword("VALIDPASS1!"), false);
});

test("rejects passwords without numeric digits", () => {
  assert.equal(isStrongPassword("ValidPass!"), false);
});

test("rejects passwords without special characters", () => {
  assert.equal(isStrongPassword("ValidPass1"), false);
});

test("returns the shared validation message for invalid passwords", () => {
  assert.equal(
    getPasswordValidationError("simple"),
    PASSWORD_VALIDATION_MESSAGE,
  );
});

test("returns requirement status for checklist rendering", () => {
  assert.deepEqual(
    getPasswordRequirementResults("#AKShat@09").map((requirement) => ({
      id: requirement.id,
      isMet: requirement.isMet,
    })),
    PASSWORD_REQUIREMENTS.map((requirement) => ({
      id: requirement.id,
      isMet: true,
    })),
  );
});
