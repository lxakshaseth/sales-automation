export const PASSWORD_VALIDATION_MESSAGE =
  "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.";

const SPECIAL_CHARACTER_PATTERN = /[^A-Za-z0-9\s]/;

export const PASSWORD_REQUIREMENTS = [
  {
    id: "minimum-length",
    label: "Minimum 8 characters",
    test: (password: string) => password.length >= 8,
  },
  {
    id: "uppercase",
    label: "At least 1 uppercase letter (A-Z)",
    test: (password: string) => /[A-Z]/.test(password),
  },
  {
    id: "lowercase",
    label: "At least 1 lowercase letter (a-z)",
    test: (password: string) => /[a-z]/.test(password),
  },
  {
    id: "number",
    label: "At least 1 number (0-9)",
    test: (password: string) => /[0-9]/.test(password),
  },
  {
    id: "special-character",
    label: "At least 1 special character (@, #, $, %, &, *, !, etc.)",
    test: (password: string) => SPECIAL_CHARACTER_PATTERN.test(password),
  },
] as const;

export const getPasswordRequirementResults = (password: unknown) => {
  const value = typeof password === "string" ? password : "";

  return PASSWORD_REQUIREMENTS.map(({ id, label, test }) => ({
    id,
    label,
    isMet: typeof password === "string" && test(value),
  }));
};

export const isStrongPassword = (password: unknown): password is string => {
  return (
    typeof password === "string" &&
    getPasswordRequirementResults(password).every((requirement) => requirement.isMet)
  );
};

export const getPasswordValidationError = (password: unknown) =>
  isStrongPassword(password) ? null : PASSWORD_VALIDATION_MESSAGE;
