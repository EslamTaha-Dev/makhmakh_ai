import { Compass } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { BrandLogo } from "@/components/brand/logo";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/routing";

export default async function NotFoundPage() {
  const t = await getTranslations("errors");

  return (
    <main
      id="main"
      className="flex min-h-dvh flex-col items-center justify-center gap-8 px-6 py-16 brand-wash text-center"
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
          {t("notFoundTitle")}
        </h1>
        <p className="mx-auto max-w-md text-sm text-muted-fg break-arabic">
          {t("notFoundBody")}
        </p>
      </div>

      <Link href="/" className={buttonVariants({ size: "lg" })}>
        {t("notFoundCta")}
      </Link>
    </main>
  );
}
