"use client";

import { Languages } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import * as React from "react";

import { usePathname, useRouter } from "@/i18n/routing";
import { cn } from "@/lib/utils";

export function LocaleSwitcher({
  className,
  variant = "ghost",
}: {
  className?: string;
  variant?: "ghost" | "outline";
}) {
  const locale = useLocale();
  const t = useTranslations("common");
  const router = useRouter();
  const pathname = usePathname();
  const [isPending, startTransition] = React.useTransition();

  const nextLocale = locale === "ar" ? "en" : "ar";

  const switchLocale = () => {
    startTransition(() => {
      router.replace(pathname, { locale: nextLocale });
    });
  };

  return (
    <button
      type="button"
      onClick={switchLocale}
      disabled={isPending}
      aria-label={`${t("language")}: ${nextLocale === "ar" ? t("arabic") : t("english")}`}
      className={cn(
        "inline-flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-medium transition",
        variant === "outline"
          ? "border border-cocoa-800/15 bg-white text-cocoa-800 hover:border-brand-500/40 hover:bg-brand-50"
          : "text-cocoa-800 hover:bg-cocoa-800/6",
        isPending && "opacity-60",
        className,
      )}
    >
      <Languages aria-hidden className="size-4" />
      <span>{nextLocale === "ar" ? "العربية" : "English"}</span>
    </button>
  );
}
