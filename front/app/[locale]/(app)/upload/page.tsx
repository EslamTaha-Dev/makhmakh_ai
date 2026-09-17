"use client";

import {
  CheckCircle2,
  Clock,
  Info,
  Loader2,
  RefreshCw,
  XCircle,
} from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import { UploadDropzone } from "@/components/materials/upload-dropzone";
import { CreateSpaceDialog } from "@/components/subjects/create-space-dialog";
import { Alert } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Field, Select } from "@/components/ui/field";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import { useMyCourses } from "@/hooks/use-courses";
import { useMaterialProcessing, useUploadMaterial } from "@/hooks/use-materials";
import { useQueryParam } from "@/hooks/use-query-param";
import { Link } from "@/i18n/routing";
import type { MaterialStatus } from "@/lib/api/types";
import {
  UPLOAD_MAX_SIZE_BYTES,
  UPLOAD_MAX_SIZE_MB,
  isAcceptedUpload,
} from "@/lib/constants";
import { cn } from "@/lib/utils";

const STATUS_ICON: Record<MaterialStatus, React.ElementType> = {
  pending: Clock,
  processing: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};

export default function UploadPage() {
  const t = useTranslations("upload");
  const tCommon = useTranslations("common");
  const describeError = useApiErrorMessage();

  const { value: spaceParam } = useQueryParam("space");
  const myCourses = useMyCourses();

  const [courseId, setCourseId] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);
  const [fileError, setFileError] = React.useState<string | null>(null);
  const [materialId, setMaterialId] = React.useState<string | null>(null);

  // Default the space to the one requested in the URL, else the first space.
  // Derived instead of stored so the selection never depends on an effect.
  const defaultCourseId = React.useMemo(() => {
    if (!myCourses.data?.length) return "";

    const requested = spaceParam
      ? myCourses.data.find((course) => course.id === spaceParam)
      : undefined;

    return requested?.id ?? myCourses.data[0].id;
  }, [spaceParam, myCourses.data]);

  const selectedCourseId = courseId || defaultCourseId;

  const upload = useUploadMaterial(selectedCourseId || "none");
  const processing = useMaterialProcessing(materialId);

  const validate = (candidate: File): boolean => {
    if (!isAcceptedUpload(candidate.name)) {
      setFileError(t("errors.unsupported"));
      return false;
    }

    if (candidate.size === 0) {
      setFileError(t("errors.empty"));
      return false;
    }

    if (candidate.size > UPLOAD_MAX_SIZE_BYTES) {
      setFileError(
        t("errors.tooLarge", { size: `${UPLOAD_MAX_SIZE_MB} MB` }),
      );
      return false;
    }

    setFileError(null);
    return true;
  };

  const handleSelect = (candidate: File) => {
    setMaterialId(null);

    if (!validate(candidate)) {
      setFile(null);
      return;
    }

    setFile(candidate);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!selectedCourseId) {
      toast.error(t("errors.noSpace"));
      return;
    }

    if (!file) {
      toast.error(t("errors.noFile"));
      return;
    }

    try {
      const material = await upload.mutateAsync(file);
      setMaterialId(material.id);
      setFile(null);
      toast.success(t("status.pending"));
    } catch (error) {
      toast.error(describeError(error, "upload"));
    }
  };

  const status = processing.data?.processing_status;
  const StatusIcon = status ? STATUS_ICON[status] : Clock;

  const statusHintKey =
    status === "completed"
      ? "completedHint"
      : status === "failed"
        ? "failedHint"
        : status === "processing"
          ? "processingHint"
          : "pendingHint";

  const statusTone =
    status === "completed"
      ? "bg-emerald-50 text-emerald-600"
      : status === "failed"
        ? "bg-red-50 text-red-600"
        : "bg-brand-50 text-brand-600";

  const reset = () => {
    setMaterialId(null);
    setFile(null);
    setFileError(null);
  };

  if (myCourses.isPending) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-56" />
        <Skeleton className="h-72" />
      </div>
    );
  }

  if (myCourses.isError) {
    return (
      <ErrorState
        title={tCommon("offlineHint")}
        onRetry={() => void myCourses.refetch()}
        retryLabel={tCommon("retry")}
      />
    );
  }

  if (!myCourses.data.length) {
    return (
      <div className="space-y-6">
        <header className="space-y-1.5">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("title")}
          </h1>
          <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
        </header>

        <EmptyState
          icon={<Info aria-hidden />}
          title={t("spaceEmpty")}
          body={t("spaceEmptyCta")}
          action={
            <CreateSpaceDialog
              navigateOnCreate
              trigger={
                <span className={cn(buttonVariants({ size: "md" }), "cursor-pointer")}>
                  {t("spaceEmptyCta")}
                </span>
              }
            />
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <header className="space-y-1.5">
        <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
          {t("title")}
        </h1>
        <p className="max-w-2xl text-sm text-muted-fg break-arabic">
          {t("subtitle")}
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr] lg:items-start">
        <Card className="p-6">
          {materialId ? (
            <div className="space-y-6" aria-live="polite">
              <CardTitle as="h2">{t("status.title")}</CardTitle>

              <div className="flex items-start gap-4 rounded-2xl border border-cocoa-800/10 bg-muted/40 p-5">
                <span
                  className={cn(
                    "flex size-12 shrink-0 items-center justify-center rounded-2xl",
                    statusTone,
                  )}
                >
                  <StatusIcon
                    aria-hidden
                    className={cn(
                      "size-6",
                      status === "processing" && "animate-spin",
                    )}
                  />
                </span>

                <div className="min-w-0 space-y-1">
                  <p className="font-medium text-cocoa-900 break-arabic">
                    {status ? t(`status.${status}`) : tCommon("loading")}
                  </p>
                  <p className="text-sm text-muted-fg break-arabic">
                    {t(`status.${statusHintKey}`)}
                  </p>

                  {processing.data ? (
                    <p className="truncate pt-1 text-xs text-muted-fg" dir="auto">
                      {processing.data.file_name}
                    </p>
                  ) : null}
                </div>
              </div>

              {processing.data?.processing_status === "failed" &&
              processing.data.error_message ? (
                <Alert tone="error" title={t("status.failed")}>
                  {processing.data.error_message}
                </Alert>
              ) : null}

              <div className="flex flex-wrap gap-3">
                {status === "completed" ? (
                  <Link
                    href={`/subjects/${processing.data?.course_id ?? selectedCourseId}`}
                    className={buttonVariants({ size: "md" })}
                  >
                    {t("status.openSpace")}
                  </Link>
                ) : null}

                {status === "failed" ? (
                  <Button variant="soft" onClick={reset}>
                    <RefreshCw aria-hidden />
                    {t("status.again")}
                  </Button>
                ) : null}

                <Button variant="outline" onClick={reset}>
                  {t("status.again")}
                </Button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6" noValidate>
              <Field label={t("space")} htmlFor="upload-space" required>
                <Select
                  id="upload-space"
                  value={selectedCourseId}
                  onChange={(event) => setCourseId(event.target.value)}
                >
                  {myCourses.data.map((course) => (
                    <option key={course.id} value={course.id}>
                      {course.name}
                    </option>
                  ))}
                </Select>
              </Field>

              <UploadDropzone
                file={file}
                onSelect={handleSelect}
                onClear={() => {
                  setFile(null);
                  setFileError(null);
                }}
                disabled={upload.isPending}
                error={fileError}
              />

              {fileError ? <Alert tone="error">{fileError}</Alert> : null}

              {upload.isError ? (
                <Alert tone="error">
                  {describeError(upload.error, "upload")}
                </Alert>
              ) : null}

              <Button
                type="submit"
                size="lg"
                block
                disabled={!file}
                loading={upload.isPending}
                loadingText={t("submitting")}
              >
                {t("submit")}
              </Button>
            </form>
          )}
        </Card>

        <Card className="p-6">
          <CardTitle as="h2" className="text-base">
            {t("guide.title")}
          </CardTitle>

          <ul className="mt-4 space-y-3">
            {(["document", "audio", "size"] as const).map((key) => (
              <li key={key} className="flex items-start gap-2.5">
                <span
                  aria-hidden
                  className="mt-1.5 size-1.5 shrink-0 rounded-full brand-gradient-surface"
                />
                <p className="text-sm leading-relaxed text-muted-fg break-arabic">
                  {t(`guide.${key}`)}
                </p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
