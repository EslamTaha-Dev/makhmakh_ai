"use client";

import { BookOpen, Lock, TrainTrack } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Link } from "@/i18n/routing";
import type { Course, MyCourse } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

type CourseCardProps = {
  course: Course | MyCourse;
  /** Optional progress percentage when we already know it. */
  progress?: number | null;
  enrolledAt?: string;
  className?: string;
};

export function CourseCard({
  course,
  progress = null,
  enrolledAt,
  className,
}: CourseCardProps) {
  const t = useTranslations("subjects");
  const locale = useLocale();

  const isPrivate = course.visibility === "private";

  return (
    <article
      className={cn(
        "group flex h-full flex-col rounded-3xl border border-cocoa-800/10 bg-white p-5 shadow-soft transition duration-300 hover:-translate-y-1 hover:border-brand-500/30 hover:shadow-lift",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="flex size-11 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 transition duration-300 group-hover:bg-brand-500 group-hover:text-white">
          {isPrivate ? (
            <Lock aria-hidden className="size-5" />
          ) : (
            <BookOpen aria-hidden className="size-5" />
          )}
        </span>

        <div className="flex flex-wrap justify-end gap-1.5">
          <Badge tone={isPrivate ? "yellow" : "neutral"}>
            {isPrivate ? t("detail.yourSpace") : t("detail.published")}
          </Badge>

        </div>
      </div>

      <h3 className="mt-4 font-display text-lg leading-snug text-cocoa-900 break-arabic">
        {course.name}
      </h3>

      <p className="mt-2 line-clamp-2 min-h-10 text-sm leading-relaxed text-muted-fg break-arabic">
        {course.description || t("detail.noDescription")}
      </p>

      {progress !== null ? (
        <div className="mt-4 flex items-center gap-2 text-xs text-cocoa-800/80">
          <TrainTrack aria-hidden className="size-3.5 text-brand-500" />
          <span className="tabular font-medium">{Math.round(progress)}%</span>
          <span className="text-muted-fg">{t("detail.progressTitle")}</span>
        </div>
      ) : enrolledAt ? (
        <p className="mt-4 text-xs text-muted-fg">
          {formatRelativeTime(enrolledAt, locale)}
        </p>
      ) : null}

      <div className="mt-5 flex items-center gap-2 pt-1">
        <Link
          href={`/subjects/${course.id}`}
          className={cn(buttonVariants({ size: "sm" }), "flex-1")}
        >
          {t("catalog.continue")}
        </Link>

        <Link
          href={`/upload?space=${course.id}`}
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          {t("detail.uploadCta")}
        </Link>
      </div>
    </article>
  );
}
