import { createNavigation } from "next-intl/navigation";
import { defineRouting } from "next-intl/routing";

export const locales = ["ar", "en"] as const;

export type Locale = (typeof locales)[number];

/** Narrows an arbitrary route param to a supported locale. */
export function isLocale(value: string): value is Locale {
  return (locales as readonly string[]).includes(value);
}

export const defaultLocale: Locale = "ar";

export const routing = defineRouting({
  locales,
  defaultLocale,
  // Arabic lives at "/", English at "/en" — Arabic-first without a forced prefix.
  localePrefix: "as-needed",
  localeDetection: false,
});

export const { Link, redirect, usePathname, useRouter, getPathname } =
  createNavigation(routing);
