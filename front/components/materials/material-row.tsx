"use client";

import { ExternalLink, FileAudio, FileText, FileVideo, AlertTriangle } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import * as React from "react";

import { MaterialStatusBadge } from "@/components/materials/status-badge";
import { Link } from "@/i18n/routing";
import type { Material } from "@/lib/api/types";
import { FILE_TYPE_LABEL } from "@/lib/constants";
import { formatDateTime } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Static lookup so the icon component is never created during render. */
const FILE_ICONS: Record<string, React.ElementType> = {
  mp3: FileAudio,
  wav: FileAudio,
  mp4: FileVideo,
  mov: FileVideo,
};

export function MaterialRow({
  material,
  showSpace = false,
  spaceName,
  className,
}: {
  material: Material;
  showSpace?: boolean;
  spaceName?: string | null;
  className?: string;
}) {
  const t = useTranslations("materials");
  const tUpload = useTranslations("upload.status");
  const locale = useLocale();

  const Icon = FILE_ICONS[material.file_type] ?? FileText;

  return (
    <article
      className={cn(
        "flex flex-wrap items-center gap-4 rounded-2xl border border-cocoa-800/10 bg-white p-4 transition duration-200 hover:border-brand-500/25 hover:shadow-soft",
        className,
      )}
    >
      <span
        className={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-xl",
          material.processing_status === "failed"
            ? "bg-red-50 text-red-600"
            : "bg-brand-50 text-brand-600",
        )}
      >
        <Icon aria-hidden className="size-5" />
      </span>

      <div className="min-w-0 flex-1">
        <p
          className="truncate text-sm font-medium text-cocoa-900"
          title={material.file_name}
        >
          {material.file_name}
        </p>

        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-fg">
          <span className="rounded-md bg-muted px-1.5 py-0.5 font-medium">
            {FILE_TYPE_LABEL[material.file_type] ?? t("unknownType")}
          </span>

          <span>{formatDateTime(material.uploaded_at, locale)}</span>

          {showSpace && spaceName ? <span>{spaceName}</span> : null}
        </div>
      </div>

      <MaterialStatusBadge status={material.processing_status} />

      {material.processing_status === "failed" ? (
        <p className="flex w-full items-start gap-1.5 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700">
          <AlertTriangle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <span className="break-arabic">
            {material.error_message || tUpload("failedHint")}
          </span>
        </p>
      ) : null}

      <Link
        href={`/subjects/${material.course_id}`}
        className="inline-flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-medium text-brand-600 transition hover:bg-brand-50"
      >
        <ExternalLink aria-hidden className="size-3.5" />
        {t("openSpace")}
      </Link>
    </article>
  );
}
