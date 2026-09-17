import { CheckCircle2 } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { RedirectIfAuthenticated } from "@/components/auth/guards";
import { BrandLockup, BrandLogo } from "@/components/brand/logo";
import { LocaleSwitcher } from "@/components/layout/locale-switcher";
import { Link } from "@/i18n/routing";

export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = await getTranslations("auth.aside");
  const tCommon = await getTranslations("common");

  const points = t.raw("points") as string[];

  return (
    <RedirectIfAuthenticated>
      <div className="grid min-h-dvh lg:grid-cols-[1.02fr_1fr]">
        {/* Brand panel — decorative, so it steps aside on small screens. */}
        <aside className="relative hidden overflow-hidden brand-wash p-10 lg:flex lg:flex-col">
          <div aria-hidden className="absolute inset-0 brand-grid" />

          <Link href="/" className="relative" aria-label={tCommon("appName")}>
            <BrandLogo height={44} priority />
          </Link>

          <div className="relative my-auto max-w-md">
            <h2 className="font-display text-3xl leading-snug text-cocoa-900">
              {t("title")}
            </h2>

            <ul className="mt-8 space-y-4">
              {points.map((point) => (
                <li key={point} className="flex items-start gap-3">
                  <CheckCircle2
                    aria-hidden
                    className="mt-0.5 size-5 shrink-0 text-brand-500"
                  />
                  <span className="text-sm leading-relaxed text-cocoa-800/85 break-arabic">
                    {point}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div className="relative flex items-end justify-between gap-4">
            <BrandLockup height={104} className="opacity-90" />
          </div>
        </aside>

        <main
          id="main"
          className="relative flex flex-col bg-white px-5 py-8 sm:px-10 lg:justify-center"
        >
          <div className="mb-8 flex items-center justify-between lg:justify-end">
            <Link href="/" className="lg:hidden" aria-label={tCommon("appName")}>
              <BrandLogo height={38} priority />
            </Link>

            <LocaleSwitcher variant="outline" />
          </div>

          <div className="mx-auto w-full max-w-md">{children}</div>
        </main>
      </div>
    </RedirectIfAuthenticated>
  );
}
