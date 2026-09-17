"use client";

import { CheckCircle2, MailWarning } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { Alert } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { Spinner } from "@/components/ui/states";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { useQueryParam } from "@/hooks/use-query-param";
import { Link } from "@/i18n/routing";
import * as api from "@/lib/api/endpoints";
import { useSessionStore } from "@/lib/auth/session-store";

type Status = "verifying" | "verified" | "failed" | "missing";

export default function VerifyEmailPage() {
  const t = useTranslations("auth.verify");
  const tCommon = useTranslations("common");
  const describeError = useApiErrorMessage();
  const { value: token, ready } = useQueryParam("token");
  const refreshUser = useSessionStore((state) => state.refreshUser);

  // Only the async outcome is stored: "verifying" and "missing" are derived,
  // so nothing has to be written from an effect body synchronously.
  const [outcome, setOutcome] = React.useState<
    { status: "verified" } | { status: "failed"; message: string } | null
  >(null);

  const status: Status =
    ready && !token ? "missing" : outcome ? outcome.status : "verifying";

  const message = outcome?.status === "failed" ? outcome.message : "";

  React.useEffect(() => {
    if (!ready || !token) return;

    let cancelled = false;

    const run = async () => {
      try {
        await api.verifyEmail({ token });
        if (cancelled) return;
        setOutcome({ status: "verified" });
        // Keep the cached profile in sync with the new verification state.
        void refreshUser();
      } catch (error) {
        if (cancelled) return;
        setOutcome({ status: "failed", message: describeError(error, "generic") });
      }
    };

    void run();

    return () => {
      cancelled = true;
    };
  }, [ready, token, describeError, refreshUser]);

  return (
    <div className="space-y-6">
      {status === "verifying" ? (
        <>
          <header className="space-y-2">
            <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
              {t("title")}
            </h1>
            <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
          </header>

          <div className="rounded-2xl border border-cocoa-800/10 bg-muted/60 px-5 py-8">
            <Spinner label={tCommon("loading")} className="text-brand-500" />
          </div>
        </>
      ) : null}

      {status === "verified" ? (
        <>
          <span className="flex size-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
            <CheckCircle2 aria-hidden className="size-7" />
          </span>

          <header className="space-y-2">
            <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
              {t("successTitle")}
            </h1>
            <p className="text-sm text-muted-fg break-arabic">{t("successBody")}</p>
          </header>

          <Link
            href="/dashboard"
            className={buttonVariants({ size: "lg", block: true })}
          >
            {t("goToDashboard")}
          </Link>
        </>
      ) : null}

      {status === "failed" || status === "missing" ? (
        <>
          <span className="flex size-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
            <MailWarning aria-hidden className="size-7" />
          </span>

          <header className="space-y-2">
            <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
              {t("errorTitle")}
            </h1>
            <p className="text-sm text-muted-fg break-arabic">{t("errorBody")}</p>
          </header>

          {status === "missing" ? (
            <Alert tone="warning">{t("missingToken")}</Alert>
          ) : message ? (
            <Alert tone="error">{message}</Alert>
          ) : null}

          <Link
            href="/settings"
            className={buttonVariants({ variant: "outline", block: true })}
          >
            {t("goToDashboard")}
          </Link>
        </>
      ) : null}
    </div>
  );
}
