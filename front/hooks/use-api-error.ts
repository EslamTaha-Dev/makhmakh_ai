"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import { describeApiError, type ErrorContext } from "@/lib/errors";

/**
 * Resolves an API error into a user-facing message using the active locale.
 * Falls back to a generic message when a key is missing from the catalogue.
 */
export function useApiErrorMessage() {
  const t = useTranslations();

  return React.useCallback(
    (error: unknown, context: ErrorContext = "generic"): string => {
      const described = describeApiError(error, context);

      if (described.kind === "raw") {
        return described.message;
      }

      // Catalogue keys are validated at runtime: a stale key falls back safely.
      const key = described.key as Parameters<typeof t>[0];

      return t.has(key) ? t(key) : t("auth.errors.generic");
    },
    [t],
  );
}
