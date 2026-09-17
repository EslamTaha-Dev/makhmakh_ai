import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";

import { LandingFaq, LandingFinalCta } from "@/components/landing/faq";
import { LandingFeatures } from "@/components/landing/features";
import { LandingHero } from "@/components/landing/hero";
import { LandingHowItWorks } from "@/components/landing/how-it-works";
import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { isLocale } from "@/i18n/routing";

export default async function LandingPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  if (!isLocale(locale)) {
    notFound();
  }

  setRequestLocale(locale);

  return (
    <>
      <SiteHeader />

      <main id="main" className="flex-1">
        <LandingHero />
        <LandingFeatures />
        <LandingHowItWorks />
        <LandingFaq />
        <LandingFinalCta />
      </main>

      <SiteFooter />
    </>
  );
}
