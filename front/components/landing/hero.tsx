"use client";

import { ArrowLeft, ArrowRight, PlayCircle, Sparkles } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { BrandMark } from "@/components/brand/logo";
import { Reveal } from "@/components/motion/reveal";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/routing";
import { useSessionStore } from "@/lib/auth/session-store";
import { cn } from "@/lib/utils";

export function LandingHero() {
  const t = useTranslations("landing.hero");
  const locale = useLocale();
  const status = useSessionStore((state) => state.status);

  const isRtl = locale === "ar";
  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  const primaryHref = status === "authenticated" ? "/dashboard" : "/register";

  const chips = [
    t("chips.ownCorpus"),
    t("chips.citedAnswers"),
    t("chips.conceptMap"),
  ];

  return (
    <section className="relative overflow-hidden brand-wash">
      <div aria-hidden className="absolute inset-0 brand-grid" />

      <div className="relative mx-auto grid max-w-7xl gap-14 px-4 py-16 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-center lg:gap-10 lg:py-24 lg:px-8">
        <div className="max-w-2xl">
          <Reveal>
            <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-white/80 px-3.5 py-1.5 text-xs font-medium text-cocoa-800 shadow-soft backdrop-blur">
              <Sparkles aria-hidden className="size-3.5 text-brand-500" />
              {t("eyebrow")}
            </span>
          </Reveal>

          {/* Aviny appears once on the whole site: the brand's own name. */}
          <Reveal delay={0.05}>
            <p
              className="font-brand mt-7 text-6xl leading-none text-brand-500 sm:text-7xl lg:text-8xl"
              aria-hidden
            >
              {t("brandStatement")}
            </p>
          </Reveal>

          <Reveal delay={0.1}>
            <h1 className="mt-4 font-display text-3xl leading-tight text-cocoa-900 text-balance sm:text-4xl lg:text-5xl">
              {t("title")}
            </h1>
          </Reveal>

          <Reveal delay={0.15}>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-muted-fg break-arabic sm:text-lg">
              {t("subtitle")}
            </p>
          </Reveal>

          <Reveal delay={0.2}>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href={primaryHref}
                className={cn(buttonVariants({ size: "lg" }), "group")}
              >
                {t("primaryCta")}
                <Arrow
                  aria-hidden
                  className="transition-transform duration-300 group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5"
                />
              </Link>

              <a
                href="#how"
                className={buttonVariants({ variant: "outline", size: "lg" })}
              >
                <PlayCircle aria-hidden />
                {t("secondaryCta")}
              </a>
            </div>
          </Reveal>

          <Reveal delay={0.25}>
            <ul className="mt-8 flex flex-wrap gap-x-5 gap-y-2">
              {chips.map((chip) => (
                <li
                  key={chip}
                  className="flex items-center gap-2 text-sm text-cocoa-800/80"
                >
                  <span
                    aria-hidden
                    className="size-1.5 rounded-full brand-gradient-surface"
                  />
                  {chip}
                </li>
              ))}
            </ul>
          </Reveal>

          <Reveal delay={0.3}>
            <p className="mt-6 text-xs text-muted-fg break-arabic">
              {t("trustLine")}
            </p>
          </Reveal>
        </div>

        <Reveal delay={0.2} className="relative">
          <div className="relative mx-auto flex max-w-sm items-center justify-center">
            <div
              aria-hidden
              className="absolute inset-x-6 bottom-6 top-10 rounded-[3rem] bg-brand-500/10 blur-2xl"
            />

            <BrandMark
              height={340}
              alt="مخمخ"
              className="relative z-10 animate-brand-float drop-shadow-[0_24px_48px_rgba(102,51,0,0.18)]"
            />
          </div>
        </Reveal>
      </div>
    </section>
  );
}
