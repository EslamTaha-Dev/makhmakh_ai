"use client";

import { BookOpen, Library, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { CourseCard } from "@/components/subjects/course-card";
import { CreateSpaceDialog } from "@/components/subjects/create-space-dialog";
import { Button, buttonVariants } from "@/components/ui/button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import {
  useCourseCatalogInfinite,
  useMyCourses,
} from "@/hooks/use-courses";
import { cn } from "@/lib/utils";

export default function SubjectsPage() {
  const t = useTranslations("subjects");
  const tCommon = useTranslations("common");

  const [tab, setTab] = React.useState<"mine" | "catalog">("mine");

  const myCourses = useMyCourses();
  const catalog = useCourseCatalogInfinite();

  const enrolledIds = React.useMemo(
    () => new Set(myCourses.data?.map((course) => course.id) ?? []),
    [myCourses.data],
  );

  const catalogItems = React.useMemo(
    () => catalog.data?.pages.flatMap((page) => page.items) ?? [],
    [catalog.data],
  );

  const tabs = [
    { key: "mine" as const, label: t("tabs.mine"), icon: Sparkles },
    { key: "catalog" as const, label: t("tabs.catalog"), icon: Library },
  ];

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-5">
        <div className="space-y-1.5">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("title")}
          </h1>
          <p className="max-w-xl text-sm text-muted-fg break-arabic">
            {t("subtitle")}
          </p>
        </div>

        <CreateSpaceDialog navigateOnCreate />
      </header>

      <div
        role="tablist"
        aria-label={t("title")}
        className="inline-flex rounded-2xl border border-cocoa-800/10 bg-white p-1 shadow-soft"
      >
        {tabs.map((item) => {
          const Icon = item.icon;
          const active = tab === item.key;

          return (
            <button
              key={item.key}
              type="button"
              role="tab"
              aria-selected={active}
              onClick={() => setTab(item.key)}
              className={cn(
                "inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition duration-200",
                active
                  ? "brand-gradient-surface text-white"
                  : "text-cocoa-800/80 hover:bg-muted",
              )}
            >
              <Icon aria-hidden className="size-4" />
              {item.label}
            </button>
          );
        })}
      </div>

      {tab === "mine" ? (
        <section aria-label={t("tabs.mine")}>
          {myCourses.isPending ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2].map((key) => (
                <Skeleton key={key} className="h-56" />
              ))}
            </div>
          ) : myCourses.isError ? (
            <ErrorState
              title={tCommon("offlineHint")}
              onRetry={() => void myCourses.refetch()}
              retryLabel={tCommon("retry")}
            />
          ) : myCourses.data.length === 0 ? (
            <EmptyState
              icon={<Sparkles aria-hidden />}
              title={t("mine.empty")}
              body={t("mine.emptyBody")}
              action={
                <CreateSpaceDialog
                  navigateOnCreate
                  trigger={
                    <span
                      className={cn(
                        buttonVariants({ size: "md" }),
                        "cursor-pointer",
                      )}
                    >
                      {t("mine.cta")}
                    </span>
                  }
                />
              }
            />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {myCourses.data.map((course) => (
                <CourseCard
                  key={course.id}
                  course={course}
                  enrolledAt={course.enrolled_at}
                />
              ))}
            </div>
          )}
        </section>
      ) : (
        <section className="space-y-5" aria-label={t("tabs.catalog")}>
          {catalog.isPending ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[0, 1, 2].map((key) => (
                <Skeleton key={key} className="h-56" />
              ))}
            </div>
          ) : catalog.isError ? (
            <ErrorState
              title={tCommon("offlineHint")}
              onRetry={() => void catalog.refetch()}
              retryLabel={tCommon("retry")}
            />
          ) : catalogItems.length === 0 ? (
            <EmptyState
              icon={<BookOpen aria-hidden />}
              title={t("catalog.empty")}
              body={t("catalog.emptyBody")}
            />
          ) : (
            <>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {catalogItems.map((course) => (
                  <CourseCard
                    key={course.id}
                    course={course}
                    className={
                      enrolledIds.has(course.id)
                        ? "ring-1 ring-brand-500/30"
                        : undefined
                    }
                  />
                ))}
              </div>

              {catalog.hasNextPage ? (
                <div className="flex justify-center">
                  <Button
                    variant="outline"
                    loading={catalog.isFetchingNextPage}
                    loadingText={t("catalog.loadingMore")}
                    onClick={() => void catalog.fetchNextPage()}
                  >
                    {t("catalog.loadMore")}
                  </Button>
                </div>
              ) : null}
            </>
          )}
        </section>
      )}
    </div>
  );
}
