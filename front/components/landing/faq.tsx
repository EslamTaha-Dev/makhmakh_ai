"use client";

import { Minus, Plus } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { Reveal } from "@/components/motion/reveal";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/routing";
import { cn } from "@/lib/utils";

type FaqItem = { q: string; a: string };

export function LandingFaq() {
  const t = useTranslations("landing.faq");

  const items = React.useMemo(
    () => (t.raw("items") as FaqItem[]) ?? [],
    [t],
  );

  const [openIndex, setOpenIndex] = React.useState<number | null>(0);

  return (
    <section id="faq" className="scroll-mt-24 bg-white py-20 sm:py-24">
      <div className="mx-auto grid max-w-7xl gap-12 px-4 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:gap-16 lg:px-8">
        <Reveal>
          <h2 className="font-display text-3xl text-cocoa-900 sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-fg break-arabic">
            {t("subtitle")}
          </p>
        </Reveal>

        <Reveal delay={0.08}>
          <ul className="divide-y divide-cocoa-800/10 border-y border-cocoa-800/10">
            {items.map((item, index) => {
              const isOpen = openIndex === index;

              return (
                <li key={item.q}>
                  <h3>
                    <button
                      type="button"
                      onClick={() => setOpenIndex(isOpen ? null : index)}
                      aria-expanded={isOpen}
                      aria-controls={`faq-panel-${index}`}
                      className="flex w-full items-start justify-between gap-4 py-5 text-start transition hover:text-brand-600"
                    >
                      <span className="font-display text-base text-cocoa-900 break-arabic sm:text-lg">
                        {item.q}
                      </span>

                      <span
                        aria-hidden
                        className={cn(
                          "mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border transition duration-300",
                          isOpen
                            ? "border-brand-500 bg-brand-500 text-white"
                            : "border-cocoa-800/20 text-cocoa-800",
                        )}
                      >
                        {isOpen ? (
                          <Minus className="size-3.5" />
                        ) : (
                          <Plus className="size-3.5" />
                        )}
                      </span>
                    </button>
                  </h3>

                  <div
                    id={`faq-panel-${index}`}
                    hidden={!isOpen}
                    className="pb-6 text-sm leading-relaxed text-muted-fg break-arabic motion-safe:animate-in motion-safe:fade-in"
                  >
                    {item.a}
                  </div>
                </li>
              );
            })}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}

export function LandingFinalCta() {
  const t = useTranslations("landing.cta");

  return (
    <section className="bg-surface py-16 sm:py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-[2rem] brand-gradient-surface px-6 py-12 text-center shadow-lift sm:px-12 sm:py-16">
            <div
              aria-hidden
              className="absolute inset-0 opacity-25 [background:radial-gradient(circle_at_20%_20%,rgba(255,255,255,0.9),transparent_55%)]"
            />

            <div className="relative mx-auto max-w-2xl">
              <h2 className="font-display text-2xl text-white sm:text-4xl">
                {t("title")}
              </h2>

              <p className="mt-4 text-sm leading-relaxed text-white/90 break-arabic sm:text-base">
                {t("subtitle")}
              </p>

              <Link
                href="/register"
                className={cn(
                  buttonVariants({ variant: "secondary", size: "lg" }),
                  "mt-8 bg-cocoa-900 text-white hover:bg-cocoa-950",
                )}
              >
                {t("button")}
              </Link>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
