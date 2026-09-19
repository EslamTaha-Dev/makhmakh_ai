"use client";

import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Lock,
  MessageSquareText,
  RefreshCw,
  UploadCloud,
} from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import * as React from "react";
import { toast } from "sonner";

import { MaterialRow } from "@/components/materials/material-row";
import { ConceptMap } from "@/components/subjects/concept-map";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { ProgressRing } from "@/components/ui/progress";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import {
  useBuildCourseGraph,
  useCourseConcepts,
  useCourseGraph,
} from "@/hooks/use-graph";
import {
  useCompleteConcept,
  useCourse,
  useCourseProgress,
  useEnrollInCourse,
  useMyCourses,
  useMyProgress,
} from "@/hooks/use-courses";
import { useCourseMaterials } from "@/hooks/use-materials";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { Link } from "@/i18n/routing";
import { cn } from "@/lib/utils";

export default function CourseDetailPage() {
  const params = useParams<{ courseId: string }>();
  const courseId = params?.courseId ?? "";

  const t = useTranslations("subjects.detail");
  const tCommon = useTranslations("common");
  const tSubjects = useTranslations("subjects");
  const locale = useLocale();
  const describeError = useApiErrorMessage();

  const course = useCourse(courseId);
  const concepts = useCourseConcepts(courseId);
  const graph = useCourseGraph(courseId);
  const progress = useCourseProgress(courseId);
  const materials = useCourseMaterials(courseId);
  const myCourses = useMyCourses();
  const myProgress = useMyProgress();

  const buildGraph = useBuildCourseGraph(courseId);
  const completeConcept = useCompleteConcept(courseId);
  const enroll = useEnrollInCourse();

  const [completingId, setCompletingId] = React.useState<string | null>(null);

  const Arrow = locale === "ar" ? ArrowLeft : ArrowRight;

  const enrolled = React.useMemo(
    () => Boolean(myCourses.data?.some((item) => item.id === courseId)),
    [myCourses.data, courseId],
  );

  const completedConceptIds = React.useMemo(
    () =>
      new Set(
        (myProgress.data ?? [])
          .filter((record) => record.status === "completed")
          .map((record) => record.concept_id),
      ),
    [myProgress.data],
  );

  const handleComplete = async (conceptId: string) => {
    setCompletingId(conceptId);

    try {
      await completeConcept.mutateAsync(conceptId);
      toast.success(t("completedBadge"));
    } catch (error) {
      toast.error(describeError(error, "generic"));
    } finally {
      setCompletingId(null);
    }
  };

  const handleEnroll = async () => {
    try {
      await enroll.mutateAsync(courseId);
      toast.success(tSubjects("catalog.enrolled"));
    } catch (error) {
      toast.error(describeError(error, "generic"));
    }
  };

  const handleBuild = async () => {
    try {
      await buildGraph.mutateAsync();
      toast.success(t("mapBuilding"));
    } catch (error) {
      toast.error(describeError(error, "generic"));
    }
  };

  if (course.isPending) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-40" />
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (course.isError || !course.data) {
    return (
      <ErrorState
        title={t("notFound")}
        onRetry={() => void course.refetch()}
        retryLabel={tCommon("retry")}
      >
        <Link
          href="/subjects"
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          {t("back")}
        </Link>
      </ErrorState>
    );
  }

  const detail = course.data;
  const isPrivate = detail.visibility === "private";
  const conceptList = concepts.data ?? [];

  return (
    <div className="space-y-8">
      <Link
        href="/subjects"
        className="inline-flex items-center gap-2 text-sm font-medium text-muted-fg transition hover:text-brand-600"
      >
        <Arrow aria-hidden className="size-4 rotate-180 rtl:rotate-0" />
        {t("back")}
      </Link>

      <header className="rounded-3xl border border-cocoa-800/10 bg-white p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div className="min-w-0 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={isPrivate ? "yellow" : "cocoa"}>
                {isPrivate ? (
                  <Lock aria-hidden />
                ) : (
                  <BookOpen aria-hidden />
                )}
                {isPrivate ? t("yourSpace") : t("published")}
              </Badge>

              {conceptList.length ? (
                <Badge tone="neutral">
                  {t("conceptsCount", { count: conceptList.length })}
                </Badge>
              ) : null}
            </div>

            <h1 className="font-display text-2xl text-cocoa-900 break-arabic sm:text-3xl">
              {detail.name}
            </h1>

            <p className="max-w-2xl text-sm leading-relaxed text-muted-fg break-arabic">
              {detail.description || t("noDescription")}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link
              href={`/upload?space=${detail.id}`}
              className={buttonVariants({ size: "md" })}
            >
              <UploadCloud aria-hidden />
              {t("uploadCta")}
            </Link>

            <Link
              href={`/chat?space=${detail.id}`}
              className={buttonVariants({ variant: "outline", size: "md" })}
            >
              <MessageSquareText aria-hidden />
              {t("chatCta")}
            </Link>

            {!enrolled && !isPrivate ? (
              <Button
                variant="soft"
                onClick={handleEnroll}
                loading={enroll.isPending}
                loadingText={tSubjects("catalog.enrolling")}
              >
                {tSubjects("catalog.enroll")}
              </Button>
            ) : null}
          </div>
        </div>
      </header>

      <section aria-label={t("progressTitle")}>
        {progress.isPending ? (
          <Skeleton className="h-28" />
        ) : (
          <Card className="flex flex-wrap items-center gap-6 p-6">
            <ProgressRing
              value={progress.data?.percent_complete ?? 0}
              size={104}
              strokeWidth={9}
            />

            <div className="min-w-0 flex-1 space-y-1.5">
              <CardTitle as="h2">{t("progressTitle")}</CardTitle>

              {progress.isError || progress.data?.lessons_total === 0 ? (
                <p className="text-sm text-muted-fg break-arabic">
                  {t("progressEmpty")}
                </p>
              ) : (
                <p className="text-sm text-muted-fg">
                  {progress.data
                    ? t("conceptsCount", {
                        count: progress.data.lessons_completed,
                      })
                    : "—"}
                </p>
              )}
            </div>
          </Card>
        )}
      </section>

      <section className="space-y-4" aria-labelledby="concept-map">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="space-y-1">
            <h2
              id="concept-map"
              className="font-display text-lg text-cocoa-900 sm:text-xl"
            >
              {t("mapTitle")}
            </h2>
            <p className="text-sm text-muted-fg break-arabic">
              {t("mapSubtitle")}
            </p>
          </div>

          {!conceptList.length && graph.data && graph.data.nodes.length === 0 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={handleBuild}
              loading={buildGraph.isPending}
              loadingText={t("mapBuilding")}
            >
              <RefreshCw aria-hidden />
              {t("mapBuild")}
            </Button>
          ) : null}
        </div>

        {concepts.isPending ? (
          <div className="space-y-3">
            {[0, 1, 2].map((key) => (
              <Skeleton key={key} className="h-24" />
            ))}
          </div>
        ) : concepts.isError ? (
          <ErrorState
            title={tCommon("offlineHint")}
            onRetry={() => void concepts.refetch()}
            retryLabel={tCommon("retry")}
          />
        ) : conceptList.length === 0 ? (
          <EmptyState
            icon={<BookOpen aria-hidden />}
            title={t("mapEmpty")}
            action={
              <Link
                href={`/upload?space=${detail.id}`}
                className={buttonVariants({ size: "md" })}
              >
                {t("uploadCta")}
              </Link>
            }
          />
        ) : (
          <ConceptMap
            concepts={conceptList}
            graph={graph.data}
            completedConceptIds={completedConceptIds}
            onComplete={handleComplete}
            completingId={completingId}
          />
        )}
      </section>

      <section className="space-y-4" aria-labelledby="course-materials">
        <div className="flex items-center justify-between gap-4">
          <h2
            id="course-materials"
            className="font-display text-lg text-cocoa-900 sm:text-xl"
          >
            {t("materialsTitle")}
          </h2>
        </div>

        {materials.isPending ? (
          <div className="space-y-3">
            {[0, 1].map((key) => (
              <Skeleton key={key} className="h-20" />
            ))}
          </div>
        ) : materials.isError ? (
          <Alert tone="warning">{tCommon("offlineHint")}</Alert>
        ) : materials.data.length === 0 ? (
          <EmptyState
            icon={<UploadCloud aria-hidden />}
            title={t("materialsEmpty")}
            action={
              <Link
                href={`/upload?space=${detail.id}`}
                className={buttonVariants({ variant: "outline", size: "md" })}
              >
                {t("uploadCta")}
              </Link>
            }
          />
        ) : (
          <div className={cn("space-y-3")}>
            {materials.data.map((material) => (
              <MaterialRow key={material.id} material={material} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
