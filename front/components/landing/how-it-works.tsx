import { AudioLines, FileText, Video } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Reveal } from "@/components/motion/reveal";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/routing";
import { UPLOAD_MAX_SIZE_MB } from "@/lib/constants";

const STEPS = ["space", "upload", "learn"] as const;

const FORMATS = [
  { key: "documents", icon: FileText },
  { key: "audio", icon: AudioLines },
  { key: "video", icon: Video },
] as const;

export async function LandingHowItWorks() {
  const t = await getTranslations("landing.how");
  const tFormats = await getTranslations("landing.formats");

  return (
    <section
      id="how"
      className="scroll-mt-24 border-y border-cocoa-800/8 bg-surface py-20 sm:py-24"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="max-w-2xl">
          <h2 className="font-display text-3xl text-cocoa-900 sm:text-4xl">
            {t("title")}
          </h2>
        </Reveal>

        <ol className="mt-14 grid gap-6 md:grid-cols-3">
          {STEPS.map((step, index) => (
            <Reveal as="li" key={step} delay={index * 0.08}>
              <div className="relative h-full rounded-3xl border border-cocoa-800/10 bg-white p-6 shadow-soft">
                <span className="tabular font-display text-5xl leading-none text-brand-500/25">
                  0{index + 1}
                </span>

                <h3 className="mt-4 font-display text-lg text-cocoa-900 break-arabic">
                  {t(`steps.${step}.title`)}
                </h3>

                <p className="mt-2 text-sm leading-relaxed text-muted-fg break-arabic">
                  {t(`steps.${step}.body`)}
                </p>
              </div>
            </Reveal>
          ))}
        </ol>

        <Reveal delay={0.1} className="mt-10">
          <Link
            href="/register"
            className={buttonVariants({ variant: "secondary", size: "lg" })}
          >
            {t("cta")}
          </Link>
        </Reveal>

        <div id="formats" className="mt-20 scroll-mt-24">
          <Reveal className="max-w-2xl">
            <h2 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
              {tFormats("title")}
            </h2>
            <p className="mt-3 text-sm text-muted-fg break-arabic">
              {tFormats("body").replace("100", String(UPLOAD_MAX_SIZE_MB))}
            </p>
          </Reveal>

          <ul className="mt-8 grid gap-4 sm:grid-cols-3">
            {FORMATS.map((format, index) => {
              const Icon = format.icon;

              return (
                <Reveal as="li" key={format.key} delay={index * 0.05}>
                  <div className="flex h-full items-start gap-3 rounded-2xl border border-cocoa-800/10 bg-white p-5">
                    <span className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-100/70 text-cocoa-800">
                      <Icon aria-hidden className="size-5" />
                    </span>

                    <p className="text-sm leading-relaxed text-cocoa-800 break-arabic">
                      {tFormats(`kinds.${format.key}`)}
                    </p>
                  </div>
                </Reveal>
              );
            })}
          </ul>
        </div>
      </div>
    </section>
  );
}
