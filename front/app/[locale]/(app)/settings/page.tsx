"use client";

import { KeyRound, LogOut, ShieldCheck, Smartphone, UserRound } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { LocaleSwitcher } from "@/components/layout/locale-switcher";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Field, Input } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/states";
import {
  useActiveSessions,
  useChangePassword,
  useRevokeAllSessions,
  useRevokeSession,
  useSetupMfa,
  useVerifyMfa,
} from "@/hooks/use-account";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { useRouter } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";
import { formatDateTime, initialsFromName } from "@/lib/format";
import { isRoleKey } from "@/lib/roles";
import { cn } from "@/lib/utils";

type Tab = "profile" | "security" | "sessions";

export default function SettingsPage() {
  const t = useTranslations("settings");
  const tCommon = useTranslations("common");
  const tRoles = useTranslations("roles");
  const tValidation = useTranslations("validation");
  const locale = useLocale();
  const router = useRouter();
  const describeError = useApiErrorMessage();

  const user = useSessionStore((state) => state.user);
  const signOut = useSessionStore((state) => state.signOut);

  const [tab, setTab] = React.useState<Tab>("profile");
  const [signingOut, setSigningOut] = React.useState(false);

  const sessions = useActiveSessions();
  const changePassword = useChangePassword();
  const revokeSession = useRevokeSession();
  const revokeAll = useRevokeAllSessions();
  const setupMfa = useSetupMfa();
  const verifyMfa = useVerifyMfa();

  // Change password form state.
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [passwordError, setPasswordError] = React.useState<string | null>(null);

  // MFA state.
  const [mfaCode, setMfaCode] = React.useState("");
  const [mfaEnabled, setMfaEnabled] = React.useState(false);

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "profile", label: t("tabs.profile"), icon: UserRound },
    { key: "security", label: t("tabs.security"), icon: ShieldCheck },
    { key: "sessions", label: t("tabs.sessions"), icon: Smartphone },
  ];

  const handleChangePassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setPasswordError(null);

    if (newPassword.length < 8) {
      setPasswordError(tValidation("passwordMin"));
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError(tValidation("passwordMismatch"));
      return;
    }

    try {
      await changePassword.mutateAsync({ currentPassword, newPassword });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      setPasswordError(describeError(error, "generic"));
    }
  };

  const handleSignOut = async () => {
    setSigningOut(true);
    try {
      await signOut();
      router.replace("/");
    } finally {
      setSigningOut(false);
    }
  };

  if (!user) {
    return <Skeleton className="h-96" />;
  }

  return (
    <div className="space-y-8">
      <header className="space-y-1.5">
        <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
      </header>

      <div
        role="tablist"
        aria-label={t("title")}
        className="inline-flex flex-wrap rounded-2xl border border-cocoa-800/10 bg-white p-1 shadow-soft"
      >
        {tabs.map((item) => {
          const Icon = item.icon;
          const active = tab === item.key;

          return (
            <button
              key={item.key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setTab(item.key)}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition duration-200",
                active
                  ? "brand-gradient-surface text-white"
                  : "text-cocoa-800/80 hover:bg-muted",
              )}
            >
              <Icon aria-hidden className="size-4" />
              {item.label}
            </button>
          );
        })}
      </div>

      {tab === "profile" ? (
        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.9fr] lg:items-start">
          <Card className="p-6">
            <CardTitle as="h2">{t("profile.title")}</CardTitle>

            <div className="mt-5 flex items-center gap-4">
              <span className="flex size-14 items-center justify-center rounded-2xl brand-gradient-surface text-lg font-medium text-white">
                {initialsFromName(user.name)}
              </span>

              <div className="min-w-0">
                <p className="truncate font-medium text-cocoa-900">{user.name}</p>
                <p className="truncate text-sm text-muted-fg" dir="ltr">
                  {user.email}
                </p>
              </div>
            </div>

            <dl className="mt-6 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl bg-muted/60 p-4">
                <dt className="text-xs text-muted-fg">{t("profile.role")}</dt>
                <dd className="mt-1 text-sm font-medium text-cocoa-900">
                  {isRoleKey(user.role) ? tRoles(user.role) : user.role}
                </dd>
              </div>

              <div className="rounded-2xl bg-muted/60 p-4">
                <dt className="text-xs text-muted-fg">{t("profile.joinedAt")}</dt>
                <dd className="mt-1 text-sm font-medium text-cocoa-900">
                  {formatDateTime(user.created_at, locale)}
                </dd>
              </div>
            </dl>

            <p className="mt-5 text-xs text-muted-fg break-arabic">
              {t("profile.readOnlyHint")}
            </p>

          </Card>

          <Card className="p-6">
            <CardTitle as="h2" className="text-base">
              {t("profile.preferences")}
            </CardTitle>

            <div className="mt-4 space-y-3">
              <p className="text-sm text-cocoa-800">
                {t("profile.languageLabel")}
              </p>
              <LocaleSwitcher variant="outline" className="justify-center" />
              <p className="text-xs text-muted-fg break-arabic">
                {t("profile.languageHint")}
              </p>
            </div>

            <div className="mt-6 border-t border-cocoa-800/8 pt-5">
              <p className="font-display text-sm text-cocoa-900">
                {t("danger.title")}
              </p>
              <p className="mt-1 text-xs text-muted-fg break-arabic">
                {t("danger.body")}
              </p>

              <Button
                variant="danger"
                size="sm"
                className="mt-3"
                onClick={handleSignOut}
                loading={signingOut}
              >
                <LogOut aria-hidden />
                {t("danger.logout")}
              </Button>
            </div>
          </Card>
        </div>
      ) : null}

      {tab === "security" ? (
        <div className="grid gap-6 lg:grid-cols-2 lg:items-start">
          <Card className="p-6">
            <CardTitle as="h2" className="flex items-center gap-2">
              <KeyRound aria-hidden className="size-4 text-brand-500" />
              {t("password.title")}
            </CardTitle>

            {passwordError ? (
              <Alert tone="error" className="mt-4">
                {passwordError}
              </Alert>
            ) : null}

            <form
              onSubmit={handleChangePassword}
              className="mt-5 space-y-4"
              noValidate
            >
              <Field label={t("password.current")} htmlFor="current-password" required>
                <Input
                  id="current-password"
                  type="password"
                  autoComplete="current-password"
                  value={currentPassword}
                  onChange={(event) => setCurrentPassword(event.target.value)}
                  required
                />
              </Field>

              <Field label={t("password.new")} htmlFor="new-password" required>
                <Input
                  id="new-password"
                  type="password"
                  autoComplete="new-password"
                  value={newPassword}
                  onChange={(event) => setNewPassword(event.target.value)}
                  minLength={8}
                  required
                />
              </Field>

              <Field label={t("password.confirm")} htmlFor="confirm-password" required>
                <Input
                  id="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  required
                />
              </Field>

              <Button
                type="submit"
                loading={changePassword.isPending}
                loadingText={t("password.submitting")}
              >
                {t("password.submit")}
              </Button>
            </form>
          </Card>

          <Card className="p-6">
            <CardTitle as="h2" className="flex items-center gap-2">
              <ShieldCheck aria-hidden className="size-4 text-brand-500" />
              {t("mfa.title")}
            </CardTitle>

            <p className="mt-3 text-sm text-muted-fg break-arabic">
              {t("mfa.body")}
            </p>

            {mfaEnabled ? (
              <Alert tone="success" className="mt-5">
                {t("mfa.enabled")}
              </Alert>
            ) : setupMfa.data ? (
              <div className="mt-5 space-y-4">
                <p className="text-sm text-muted-fg break-arabic">
                  {t("mfa.scanHint")}
                </p>

                <div className="rounded-2xl bg-muted/60 p-4">
                  <p className="text-xs text-muted-fg">{t("mfa.secretLabel")}</p>
                  <p
                    className="mt-1 font-mono text-sm break-all text-cocoa-900"
                    dir="ltr"
                  >
                    {setupMfa.data.secret}
                  </p>
                </div>

                <Field label={t("mfa.codeLabel")} htmlFor="mfa-code">
                  <Input
                    id="mfa-code"
                    inputMode="numeric"
                    dir="ltr"
                    maxLength={6}
                    placeholder={t("mfa.placeholderCode")}
                    value={mfaCode}
                    onChange={(event) => setMfaCode(event.target.value.trim())}
                  />
                </Field>

                <Button
                  loading={verifyMfa.isPending}
                  loadingText={t("mfa.confirming")}
                  onClick={async () => {
                    try {
                      await verifyMfa.mutateAsync(mfaCode);
                      setMfaEnabled(true);
                      toast.success(t("mfa.enabled"));
                    } catch (error) {
                      toast.error(describeError(error, "generic"));
                    }
                  }}
                >
                  {t("mfa.confirm")}
                </Button>
              </div>
            ) : (
              <Button
                variant="outline"
                className="mt-5"
                loading={setupMfa.isPending}
                loadingText={t("mfa.setup")}
                onClick={async () => {
                  try {
                    await setupMfa.mutateAsync();
                  } catch (error) {
                    toast.error(describeError(error, "generic"));
                  }
                }}
              >
                {t("mfa.enable")}
              </Button>
            )}
          </Card>
        </div>
      ) : null}

      {tab === "sessions" ? (
        <Card className="p-6">
          <CardTitle as="h2">{t("sessions.title")}</CardTitle>
          <p className="mt-3 text-sm text-muted-fg break-arabic">
            {t("sessions.body")}
          </p>

          <div className="mt-5">
            {sessions.isPending ? (
              <div className="space-y-3">
                {[0, 1].map((key) => (
                  <Skeleton key={key} className="h-20" />
                ))}
              </div>
            ) : sessions.isError ? (
              <Alert tone="warning">{tCommon("offlineHint")}</Alert>
            ) : sessions.data.length === 0 ? (
              <p className="text-sm text-muted-fg">{t("sessions.empty")}</p>
            ) : (
              <ul className="space-y-3">
                {sessions.data.map((session) => (
                  <li
                    key={session.id}
                    className="flex flex-wrap items-center gap-4 rounded-2xl border border-cocoa-800/10 bg-white p-4"
                  >
                    <span className="flex size-10 items-center justify-center rounded-xl bg-muted text-cocoa-800/70">
                      <Smartphone aria-hidden className="size-5" />
                    </span>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-cocoa-900">
                        {session.device_label || t("sessions.unknownDevice")}
                      </p>

                      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-fg">
                        {session.ip_address ? (
                          <span dir="ltr">
                            {t("sessions.ip")}: {session.ip_address}
                          </span>
                        ) : null}
                        <span>
                          {t("sessions.started")}:{" "}
                          {formatDateTime(session.created_at, locale)}
                        </span>
                        <span>
                          {t("sessions.expires")}:{" "}
                          {formatDateTime(session.expires_at, locale)}
                        </span>
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"                    loading={
                      revokeSession.isPending &&
                      revokeSession.variables === session.id
                    }
                      loadingText={t("sessions.revoking")}
                      onClick={async () => {
                        await revokeSession.mutateAsync(session.id);
                        toast.success(t("sessions.revoked"));
                      }}
                    >
                      {t("sessions.revoke")}
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {sessions.data?.length ? (
            <div className="mt-6 border-t border-cocoa-800/8 pt-5">
              <p className="text-xs text-muted-fg break-arabic">
                {t("sessions.revokeAllHint")}
              </p>

              <Button
                variant="danger"
                size="sm"
                className="mt-3"                    loading={revokeAll.isPending}
                    loadingText={t("sessions.revoking")}
                    onClick={async () => {
                      await revokeAll.mutateAsync();
                      toast.success(t("sessions.revokedAll"));
                    }}
              >
                {t("sessions.revokeAll")}
              </Button>
            </div>
          ) : null}
        </Card>
      ) : null}
    </div>
  );
}
