"use client";

import { FolderOpen, UploadCloud } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { MaterialRow } from "@/components/materials/material-row";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { useMyCourses } from "@/hooks/use-courses";
import { useMyMaterials } from "@/hooks/use-materials";
import { Link } from "@/i18n/routing";
import type { MaterialStatus } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const FILTERS: (MaterialStatus | "all")[] = [
  "all",
  "processing",
  "completed",
  "failed",
];

export default function MaterialsPage() {
  const t = useTranslations("materials");
  const tCommon = useTranslations("common");
  const tStatus = useTranslations("status");

  const [filter, setFilter] = React.useState<MaterialStatus | "all">("all");

  const materials = useMyMaterials();
  const myCourses = useMyCourses();

  const spaceNames = React.useMemo(
    () =>
      new Map(
        (myCourses.data ?? []).map((course) => [course.id, course.name]),
      ),
    [myCourses.data],
  );

  const items = React.useMemo(() => {
    const list = materials.data ?? [];
    if (filter === "all") return list;
    return list.filter((material) => material.processing_status === filter);
  }, [materials.data, filter]);

  if (materials.isPending) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="space-y-3">
          {[0, 1, 2].map((key) => (
            <Skeleton key={key} className="h-20" />
          ))}
        </div>
      </div>
    );
  }

  if (materials.isError) {
    return (
      <ErrorState
        title={tCommon("offlineHint")}
        onRetry={() => void materials.refetch()}
        retryLabel={tCommon("retry")}
      />
    );
  }

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-5">
        <div className="space-y-1.5">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("title")}
          </h1>
          <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
        </div>

        <Link href="/upload" className={buttonVariants({ size: "md" })}>
          <UploadCloud aria-hidden />
          {t("emptyCta")}
        </Link>
      </header>

      {materials.data.length === 0 ? (
        <EmptyState
          icon={<FolderOpen aria-hidden />}
          title={t("empty")}
          body={t("emptyBody")}
          action={
            <Link href="/upload" className={buttonVariants({ size: "md" })}>
              {t("emptyCta")}
            </Link>
          }
        />
      ) : (
        <>
          <div
            role="group"
            aria-label={t("status")}
            className="flex flex-wrap gap-2"
          >
            {FILTERS.map((value) => {
              const active = filter === value;
              const count =
                value === "all"
                  ? materials.data.length
                  : materials.data.filter(
                      (material) => material.processing_status === value,
                    ).length;

              return (
                <button
                  key={value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setFilter(value)}
                  className={cn(
                    "rounded-full border px-3.5 py-1.5 text-xs font-medium transition duration-200",
                    active
                      ? "border-transparent brand-gradient-surface text-white"
                      : "border-cocoa-800/12 bg-white text-cocoa-800/80 hover:border-brand-500/30 hover:text-cocoa-900",
                  )}
                >
                  {value === "all" ? tCommon("all") : tStatus(value)}
                  <span className="tabular ms-1.5 opacity-70">{count}</span>
                </button>
              );
            })}
          </div>

          {items.length === 0 ? (
            <EmptyState
              icon={<FolderOpen aria-hidden />}
              title={t("empty")}
              body={t("emptyBody")}
            />
          ) : (
            <div className="space-y-3">
              {items.map((material) => (
                <MaterialRow
                  key={material.id}
                  material={material}
                  showSpace
                  spaceName={spaceNames.get(material.course_id) ?? null}
                />
              ))}
            </div>
          )}

          <div className="flex flex-wrap gap-2 pt-2">
            <Badge tone="neutral">
              {materials.data.length} — {t("title")}
            </Badge>
          </div>
        </>
      )}
    </div>
  );
}
