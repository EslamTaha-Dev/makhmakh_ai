"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import { BrandMark } from "@/components/brand/logo";
import { Spinner } from "@/components/ui/states";
import { usePathname, useRouter } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";

export function BrandedSplash({ label }: { label?: string }) {
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 brand-wash">
      <BrandMark height={132} alt="مخمخ" className="animate-brand-float" />
      <Spinner label={label} className="text-brand-500" />
    </div>
  );
}

/** Blocks a route until the session is known, then redirects guests to sign in. */
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const t = useTranslations("common");
  const status = useSessionStore((state) => state.status);
  const router = useRouter();
  const pathname = usePathname();

  React.useEffect(() => {
    if (status === "guest") {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    }
  }, [status, router, pathname]);

  if (status !== "authenticated") {
    return <BrandedSplash label={t("loading")} />;
  }

  return <>{children}</>;
}

/** Keeps signed-in users away from the auth screens. */
export function RedirectIfAuthenticated({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = useTranslations("common");
  const status = useSessionStore((state) => state.status);
  const router = useRouter();

  React.useEffect(() => {
    if (status === "authenticated") {
      router.replace("/dashboard");
    }
  }, [status, router]);

  if (status === "loading" || status === "authenticated") {
    return <BrandedSplash label={t("loading")} />;
  }

  return <>{children}</>;
}
