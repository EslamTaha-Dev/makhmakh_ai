import type { Metadata, Viewport } from "next";
import { getMessages, getTranslations, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { fontVariables } from "@/app/fonts";
import "../globals.css";
import { Providers } from "@/components/layout/providers";
import { SessionBootstrap } from "@/components/layout/session-bootstrap";
import { isLocale, routing } from "@/i18n/routing";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export const viewport: Viewport = {
  themeColor: "#FF5900",
  width: "device-width",
  initialScale: 1,
};

type LocaleLayoutProps = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: rawLocale } = await params;
  const locale = isLocale(rawLocale) ? rawLocale : routing.defaultLocale;
  const t = await getTranslations({ locale, namespace: "meta" });

  return {
    metadataBase: new URL(
      process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
    ),
    alternates: {
      canonical: locale === routing.defaultLocale ? "/" : `/${locale}`,
      languages: {
        ar: "/",
        en: "/en",
      },
    },
    title: {
      default: t("title"),
      template: `%s · ${t("title").split("—")[0].trim()}`,
    },
    description: t("description"),
    applicationName: "Makhmakh AI",
    icons: { icon: "/brand/makhmakh-icon.png" },
    openGraph: {
      title: t("title"),
      description: t("description"),
      siteName: "Makhmakh AI",
      type: "website",
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: LocaleLayoutProps) {
  const { locale } = await params;

  if (!isLocale(locale)) {
    notFound();
  }

  setRequestLocale(locale);

  const messages = await getMessages();
  const tCommon = await getTranslations({ locale, namespace: "common" });
  const direction = locale === "ar" ? "rtl" : "ltr";

  return (
    <html lang={locale} dir={direction} className={fontVariables}>
      <body className="flex min-h-dvh flex-col bg-white text-ink antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:start-4 focus:z-[60] focus:rounded-xl focus:bg-cocoa-900 focus:px-4 focus:py-2 focus:text-sm focus:text-white"
        >
          {tCommon("skipToContent")}
        </a>

        <Providers
          locale={locale}
          messages={messages as Record<string, unknown>}
          timeZone="Africa/Cairo"
        >
          <SessionBootstrap />
          {children}
        </Providers>
      </body>
    </html>
  );
}
