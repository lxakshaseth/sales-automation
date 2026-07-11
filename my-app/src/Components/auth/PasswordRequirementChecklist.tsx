import { Check, X } from "lucide-react";
import { getPasswordRequirementResults } from "@/lib/passwordValidation";

type PasswordRequirementChecklistProps = {
  password: string;
  id?: string;
  className?: string;
};

const COMPACT_REQUIREMENT_LABELS: Record<string, string> = {
  "minimum-length": "8+ chars",
  uppercase: "A-Z",
  lowercase: "a-z",
  number: "123",
  "special-character": "Symbol",
};

const STRENGTH_STATES = {
  weak: {
    label: "Weak password",
    dotClassName: "bg-red-500",
    textClassName: "text-red-600",
  },
  medium: {
    label: "Medium password",
    dotClassName: "bg-orange-500",
    textClassName: "text-orange-600",
  },
  strong: {
    label: "Strong password",
    dotClassName: "bg-green-500",
    textClassName: "text-green-700",
  },
} as const;

export default function PasswordRequirementChecklist({
  password,
  id = "password-requirements",
  className = "",
}: PasswordRequirementChecklistProps) {
  const requirements = getPasswordRequirementResults(password);
  const hasPassword = password.length > 0;
  const completedCount = requirements.filter(
    (requirement) => requirement.isMet,
  ).length;
  const strength =
    completedCount === requirements.length
      ? STRENGTH_STATES.strong
      : completedCount >= 3
        ? STRENGTH_STATES.medium
        : STRENGTH_STATES.weak;

  return (
    <div id={id} className={`flex flex-col gap-1.5 ${className}`}>
      <ul
        className="m-0 flex list-none flex-wrap items-center gap-1.5 p-0 md:flex-nowrap"
        aria-label="Password requirements"
      >
        {requirements.map((requirement) => {
          const label =
            COMPACT_REQUIREMENT_LABELS[requirement.id] ?? requirement.label;

          return (
            <li
              key={requirement.id}
              aria-label={`${label} requirement ${
                requirement.isMet ? "satisfied" : "not satisfied"
              }`}
              className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[11px] font-semibold leading-none whitespace-nowrap transition-colors duration-200 ${
                requirement.isMet
                  ? "border-green-200 bg-green-50 text-green-700"
                  : "border-slate-200 bg-slate-50 text-slate-500"
              }`}
            >
              <span
                aria-hidden="true"
                className={`flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full transition-colors duration-200 ${
                  requirement.isMet
                    ? "bg-green-600 text-white"
                    : "bg-red-100 text-red-500"
                }`}
              >
                {requirement.isMet ? (
                  <Check className="h-2.5 w-2.5" strokeWidth={3} />
                ) : (
                  <X className="h-2.5 w-2.5" strokeWidth={3} />
                )}
              </span>
              <span>{label}</span>
            </li>
          );
        })}
      </ul>
      {hasPassword && (
        <p
          aria-live="polite"
          className={`m-0 inline-flex items-center gap-1.5 text-[11px] font-semibold leading-none transition-colors duration-200 ${strength.textClassName}`}
        >
          <span
            aria-hidden="true"
            className={`h-2 w-2 rounded-full ${strength.dotClassName}`}
          />
          <span>{strength.label}</span>
          <span className="sr-only">
            {completedCount} of {requirements.length} password requirements
            satisfied.
          </span>
        </p>
      )}
    </div>
  );
}
