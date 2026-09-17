import { ApiError } from "@/lib/api/client";

export type ErrorContext =
  | "login"
  | "register"
  | "forgot"
  | "reset"
  | "upload"
  | "chat"
  | "generic";

export type ApiErrorDescription =
  | { kind: "key"; key: string }
  | { kind: "raw"; message: string };

const RAW_FALLBACK_MIN_LENGTH = 6;

/** The backend reports these as plain English strings, so match on markers. */
function matches(detail: string, markers: string[]): boolean {
  const lower = detail.toLowerCase();
  return markers.some((marker) => lower.includes(marker));
}

export function describeApiError(
  error: unknown,
  context: ErrorContext = "generic",
): ApiErrorDescription {
  if (error instanceof ApiError) {
    const detail = error.message ?? "";

    if (error.status === 0) {
      return { kind: "key", key: "common.offlineHint" };
    }

    if (error.status === 401) {
      if (context === "reset") {
        return { kind: "key", key: "auth.reset.missingToken" };
      }

      if (context === "login" || context === "register") {
        return { kind: "key", key: "auth.errors.invalidCredentials" };
      }

      return { kind: "key", key: "errors.unauthorizedTitle" };
    }

    if (error.status === 403) {
      if (matches(detail, ["mfa", "two-factor", "verification"])) {
        return { kind: "key", key: "settings.mfa.unavailable" };
      }

      if (context === "upload") {
        return { kind: "key", key: "upload.errors.forbidden" };
      }

      return { kind: "key", key: "errors.unauthorizedBody" };
    }

    if (error.status === 404) {
      if (context === "upload") {
        return { kind: "key", key: "upload.errors.notFound" };
      }

      return { kind: "key", key: "errors.notFoundTitle" };
    }

    if (error.status === 409) {
      if (matches(detail, ["already registered", "already exists", "email"])) {
        return { kind: "key", key: "auth.errors.emailTaken" };
      }

      return { kind: "key", key: "auth.errors.generic" };
    }

    if (error.status === 413) {
      return { kind: "key", key: "upload.errors.tooLarge" };
    }

    if (error.status === 423) {
      return { kind: "key", key: "auth.errors.accountLocked" };
    }

    if (error.status === 429) {
      return { kind: "key", key: "auth.errors.rateLimited" };
    }

    if (error.status === 503) {
      if (context === "chat" || matches(detail, ["ai", "assistant"])) {
        return { kind: "key", key: "chat.notConfigured" };
      }

      if (context === "upload" || matches(detail, ["queue"])) {
        return { kind: "key", key: "upload.errors.queue" };
      }

      return { kind: "key", key: "auth.errors.notConfigured" };
    }

    if (error.status === 400) {
      if (context === "upload") {
        if (matches(detail, ["does not match", "declared file type"])) {
          return { kind: "key", key: "upload.errors.signature" };
        }

        if (matches(detail, ["empty"])) {
          return { kind: "key", key: "upload.errors.empty" };
        }

        if (matches(detail, ["unsupported", "file type"])) {
          return { kind: "key", key: "upload.errors.unsupported" };
        }
      }

      if (matches(detail, ["verification", "reset"]) && detail) {
        return { kind: "raw", message: detail };
      }
    }

    // 422 validation details are already descriptive, so surface them untouched.
    if (error.status === 422 && detail.length >= RAW_FALLBACK_MIN_LENGTH) {
      return { kind: "raw", message: detail };
    }

    if (detail && detail.length >= RAW_FALLBACK_MIN_LENGTH) {
      return { kind: "raw", message: detail };
    }

    return { kind: "key", key: "auth.errors.generic" };
  }

  if (error instanceof Error && error.message) {
    return { kind: "raw", message: error.message };
  }

  return { kind: "key", key: "auth.errors.generic" };
}
