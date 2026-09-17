import {
  Clapperboard,
  FileStack,
  GitBranch,
  LineChart,
  MessageSquareQuote,
  Upload,
} from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Reveal } from "@/components/motion/reveal";

const ITEMS = [
  { key: "upload", icon: Upload },
  { key: "understand", icon: FileStack },
  { key: "concepts", icon: GitBranch },
  { key: "assistant", icon: MessageSquareQuote },
  { key: "lessons", icon: Clapperboard },
  { key: "progress", icon: LineChart },
] as const;

export async function LandingFeatures() {
  const t = await getTranslations("landing.features");

  return (
    <section id="features" className="scroll-mt-24 bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="max-w-2xl">
          <h2 className="font-display text-3xl text-cocoa-900 sm:text-4xl">
            {t("title")}
          </h2>
          <p className="mt-4 text-base leading-relaxed text-muted-fg break-arabic">
            {t("subtitle")}
          </p>
        </Reveal>

        <ul className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {ITEMS.map((item, index) => {
            const Icon = item.icon;

            return (
              <Reveal as="li" key={item.key} delay={index * 0.05}>
                <article className="group h-full rounded-3xl border border-cocoa-800/10 bg-white p-6 shadow-soft transition duration-300 hover:-translate-y-1 hover:border-brand-500/30 hover:shadow-lift">
                  <span className="flex size-12 items-center justify-center rounded-2xl bg-brand-50 text-brand-500 transition duration-300 group-hover:bg-brand-500 group-hover:text-white">
                    <Icon aria-hidden className="size-6" />
                  </span>

                  <h3 className="mt-5 font-display text-lg text-cocoa-900 break-arabic">
                    {t(`items.${item.key}.title`)}
                  </h3>

                  <p className="mt-2 text-sm leading-relaxed text-muted-fg break-arabic">
                    {t(`items.${item.key}.body`)}
                  </p>
                </article>
              </Reveal>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
