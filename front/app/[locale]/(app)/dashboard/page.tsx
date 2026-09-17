"use client";

import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  FolderOpen,
  MessageSquareText,
  Plus,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";

import { StatCard } from "@/components/dashboard/stat-card";
import { CourseCard } from "@/components/subjects/course-card";
import { CreateSpaceDialog } from "@/components/subjects/create-space-dialog";
import { MaterialRow } from "@/components/materials/material-row";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { useConversations } from "@/hooks/use-chat";
import { useCourseCatalog, useMyCourses, useMyProgress } from "@/hooks/use-courses";
import { useMyMaterials } from "@/hooks/use-materials";
import { Link } from "@/i18n/routing";
import { useCurrentUser } from "@/lib/auth/session-store";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");
  const locale = useLocale();
  const user = useCurrentUser();

  const myCourses = useMyCourses();
  const myMaterials = useMyMaterials();
  const myProgress = useMyProgress();
  const conversations = useConversations();
  const catalog = useCourseCatalog();

  const completedConcepts =
    myProgress.data?.filter((record) => record.status === "completed").length ??
    0;

  const Arrow = locale === "ar" ? ArrowLeft : ArrowRight;

  const quickActions = [
    {
      key: "newSpace",
      href: null,
      icon: Plus,
    },
    {
      key: "upload",
      href: "/upload",
      icon: UploadCloud,
    },
    {
      key: "chat",
      href: "/chat",
      icon: MessageSquareText,
    },
  ] as const;

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-5">
        <div className="space-y-1.5">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("greeting", { name: user?.name?.split(" ")[0] ?? "" })}
          </h1>
          <p className="max-w-xl text-sm text-muted-fg break-arabic">
            {t("subtitle")}
          </p>
        </div>

        <CreateSpaceDialog />
      </header>

      <section
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
        aria-label={t("stats.spaces")}
      >
        <StatCard
          label={t("stats.spaces")}
          value={myCourses.data?.length ?? 0}
          icon={Plus}
          loading={myCourses.isPending}
        />
        <StatCard
          label={t("stats.materials")}
          value={myMaterials.data?.length ?? 0}
          icon={FolderOpen}
          loading={myMaterials.isPending}
        />
        <StatCard
          label={t("stats.completed")}
          value={completedConcepts}
          icon={CheckCircle2}
          loading={myProgress.isPending}
        />
        <StatCard
          label={t("stats.conversations")}
          value={conversations.data?.length ?? 0}
          icon={MessageSquareText}
          loading={conversations.isPending}
        />
      </section>

      <section className="space-y-4" aria-labelledby="quick-actions">
        <h2
          id="quick-actions"
          className="font-display text-lg text-cocoa-900 sm:text-xl"
        >
          {t("quickActions")}
        </h2>

        <div className="grid gap-4 sm:grid-cols-3">
          {quickActions.map((action) => {
            const Icon = action.icon;
            const content = (
              <div className="flex h-full flex-col items-start gap-3 rounded-3xl border border-cocoa-800/10 bg-white p-5 text-start shadow-soft transition duration-300 hover:-translate-y-1 hover:border-brand-500/30 hover:shadow-lift">
                <span className="flex size-11 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
                  <Icon aria-hidden className="size-5" />
                </span>

                <p className="font-display text-base text-cocoa-900">
                  {t(`actions.${action.key}`)}
                </p>

                <p className="text-xs leading-relaxed text-muted-fg break-arabic">
                  {t(`actions.${action.key}Hint`)}
                </p>
              </div>
            );

            if (action.href) {
              return (
                <Link key={action.key} href={action.href} className="block h-full">
                  {content}
                </Link>
              );
            }

            return (
              <CreateSpaceDialog
                key={action.key}
                navigateOnCreate
                trigger={content}
              />
            );
          })}
        </div>
      </section>

      <section className="space-y-4" aria-labelledby="my-spaces">
        <div className="flex items-center justify-between gap-4">
          <h2 id="my-spaces" className="font-display text-lg text-cocoa-900 sm:text-xl">
            {t("mySpaces.title")}
          </h2>

          <Link
            href="/subjects"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline"
          >
            {t("mySpaces.viewAll")}
            <Arrow aria-hidden className="size-3.5" />
          </Link>
        </div>

        {myCourses.isPending ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[0, 1, 2].map((key) => (
              <Skeleton key={key} className="h-52" />
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
            title={t("mySpaces.empty")}
            action={
              <CreateSpaceDialog
                navigateOnCreate
                trigger={
                  <span className={cn(buttonVariants({ size: "md" }), "cursor-pointer")}>
                    {t("mySpaces.emptyCta")}
                  </span>
                }
              />
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {myCourses.data.slice(0, 3).map((course) => (
              <CourseCard
                key={course.id}
                course={course}
                enrolledAt={course.enrolled_at}
              />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-4" aria-labelledby="recent-materials">
        <div className="flex items-center justify-between gap-4">
          <h2
            id="recent-materials"
            className="font-display text-lg text-cocoa-900 sm:text-xl"
          >
            {t("recentMaterials.title")}
          </h2>

          <Link
            href="/materials"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline"
          >
            {t("recentMaterials.viewAll")}
            <Arrow aria-hidden className="size-3.5" />
          </Link>
        </div>

        {myMaterials.isPending ? (
          <div className="space-y-3">
            {[0, 1].map((key) => (
              <Skeleton key={key} className="h-20" />
            ))}
          </div>
        ) : myMaterials.isError ? (
          <ErrorState
            title={tCommon("offlineHint")}
            onRetry={() => void myMaterials.refetch()}
            retryLabel={tCommon("retry")}
          />
        ) : myMaterials.data.length === 0 ? (
          <EmptyState
            icon={<UploadCloud aria-hidden />}
            title={t("recentMaterials.empty")}
            action={
              <Link
                href="/upload"
                className={buttonVariants({ variant: "outline", size: "md" })}
              >
                {t("recentMaterials.emptyCta")}
              </Link>
            }
          />
        ) : (
          <div className="space-y-3">
            {myMaterials.data.slice(0, 4).map((material) => (
              <MaterialRow key={material.id} material={material} />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-4" aria-labelledby="library-teaser">
        <div className="flex items-center justify-between gap-4">
          <h2
            id="library-teaser"
            className="font-display text-lg text-cocoa-900 sm:text-xl"
          >
            {t("catalogTeaser.title")}
          </h2>

          <Link
            href="/subjects"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline"
          >
            {t("catalogTeaser.browse")}
            <Arrow aria-hidden className="size-3.5" />
          </Link>
        </div>

        {catalog.isPending ? (
          <Skeleton className="h-52" />
        ) : catalog.isError ? (
          <Card>
            <div className="p-6">
              <CardTitle as="p" className="text-base">
                {tCommon("offlineHint")}
              </CardTitle>
            </div>
          </Card>
        ) : catalog.data.items.length === 0 ? (
          <EmptyState
            icon={<FolderOpen aria-hidden />}
            title={t("catalogTeaser.empty")}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {catalog.data.items.slice(0, 3).map((course) => (
              <CourseCard key={course.id} course={course} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
