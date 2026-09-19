import { ApiError } from "@/lib/api/client";

export type ErrorContext =
  | "login"
  | "register"
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

function getErrorCode(error: ApiError): string | null {
  if (!error.payload || typeof error.payload !== "object") return null;

  const detail = (error.payload as { detail?: unknown }).detail;
  if (!detail || typeof detail !== "object") return null;

  const code = (detail as { code?: unknown }).code;
  return typeof code === "string" ? code : null;
}

export function describeApiError(
  error: unknown,
  context: ErrorContext = "generic",
): ApiErrorDescription {
  if (error instanceof ApiError) {
    const detail = error.message ?? "";
    const errorCode = getErrorCode(error);

    if (error.status === 0) {
      return { kind: "key", key: "common.offlineHint" };
    }

    if (error.status === 401) {
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

    if ((error.status === 502 || error.status === 503) && context === "chat") {
      const chatErrorKeys: Record<string, string> = {
        AI_NOT_CONFIGURED: "chat.notConfigured",
        AI_CREDENTIAL_REJECTED: "chat.credentialRejected",
        AI_RATE_LIMITED: "chat.rateLimited",
        AI_PROVIDER_UNREACHABLE: "chat.providerUnreachable",
        AI_PROVIDER_CREDITS: "chat.providerCredits",
        AI_PROVIDER_ERROR: "chat.providerError",
        AI_PROVIDER_UNAVAILABLE: "chat.providerUnreachable",
      };

      return {
        kind: "key",
        key: (errorCode && chatErrorKeys[errorCode]) || "chat.providerError",
      };
    }

    if (error.status === 503) {
      if (matches(detail, ["ai", "assistant"])) {
        return { kind: "key", key: "chat.providerUnreachable" };
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
