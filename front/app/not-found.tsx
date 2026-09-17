import { Compass } from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { fontVariables } from "@/app/fonts";
import "./globals.css";
import { BrandLogo } from "@/components/brand/logo";
import { buttonVariants } from "@/components/ui/button";

export const metadata: Metadata = {
  title: "الصفحة مش موجودة · مخمخ",
};

/**
 * Branded 404 for paths that never reach the `[locale]` segment (for example a
 * typo'd URL). It stays fully static — no request APIs — so the rest of the app
 * keeps its prerendered output, and the copy is hardcoded Arabic-first with an
 * English line for everyone else.
 */
export default function RootNotFound() {
  return (
    <div
      lang="ar"
      dir="rtl"
      className={`${fontVariables} flex min-h-dvh flex-col items-center justify-center gap-8 bg-surface px-6 py-16 text-center`}
    >
      <Link href="/" aria-label="مخمخ">
        <BrandLogo height={48} priority />
      </Link>

      <span className="flex size-16 items-center justify-center rounded-3xl bg-white text-brand-500 shadow-soft">
        <Compass aria-hidden className="size-8" />
      </span>

      <div className="space-y-3">
        <p className="tabular font-display text-5xl text-brand-500">404</p>

        <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
          الصفحة مش موجودة
        </h1>

        <p className="mx-auto max-w-md text-sm text-muted-fg break-arabic">
          الرابط اللي فتحته مش موجود أو اتنقل. ارجع للصفحة الرئيسية وكمّل من هناك.
        </p>

        <p className="text-xs text-muted-fg" dir="ltr">
          This page could not be found.
        </p>
      </div>

      <Link href="/" className={buttonVariants({ size: "lg" })}>
        رجوع للرئيسية
      </Link>
    </div>
  );
}
