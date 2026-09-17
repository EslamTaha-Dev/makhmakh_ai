"use client";

import { FileUp, X } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { formatFileSize } from "@/lib/format";
import {
  UPLOAD_ACCEPT_ATTR,
  UPLOAD_MAX_SIZE_MB,
} from "@/lib/constants";
import { cn } from "@/lib/utils";

export function UploadDropzone({
  file,
  onSelect,
  onClear,
  disabled = false,
  error,
}: {
  file: File | null;
  onSelect: (file: File) => void;
  onClear: () => void;
  disabled?: boolean;
  error?: string | null;
}) {
  const t = useTranslations("upload");
  const tDrop = useTranslations("upload.dropzone");
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  const openPicker = () => {
    if (disabled) return;
    inputRef.current?.click();
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const dropped = event.dataTransfer.files?.[0];
    if (dropped) onSelect(dropped);
  };

  return (
    <div className="space-y-3">
      <input
        ref={inputRef}
        type="file"
        accept={UPLOAD_ACCEPT_ATTR}
        className="sr-only"
        onChange={(event) => {
          const selected = event.target.files?.[0];
          if (selected) onSelect(selected);
          // Allow re-selecting the same file after a validation error.
          event.target.value = "";
        }}
      />

      <div
        role="button"
        tabIndex={0}
        aria-label={tDrop("browse")}
        aria-disabled={disabled}
        onClick={openPicker}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openPicker();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed px-6 py-12 text-center transition duration-300",
          isDragging
            ? "border-brand-500 bg-brand-50/70"
            : "border-cocoa-800/20 bg-white hover:border-brand-500/50 hover:bg-brand-50/40",
          disabled && "pointer-events-none opacity-60",
          error && "border-red-300",
        )}
      >
        <span
          className={cn(
            "flex size-14 items-center justify-center rounded-2xl transition",
            isDragging ? "bg-brand-500 text-white" : "bg-brand-50 text-brand-600",
          )}
        >
          <FileUp aria-hidden className="size-7" />
        </span>

        <div className="space-y-1">
          <p className="font-display text-base text-cocoa-900 break-arabic">
            {tDrop("idle")}
          </p>
          <p className="text-xs text-muted-fg break-arabic">{tDrop("hint")}</p>
        </div>

        <span className="rounded-full bg-muted px-3 py-1 text-[11px] text-muted-fg">
          {tDrop("accepted")}
        </span>

        <span className="text-[11px] text-muted-fg">
          {tDrop("sizeLimit", { size: `${UPLOAD_MAX_SIZE_MB} MB` })}
        </span>
      </div>

      {file ? (
        <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-cocoa-800/10 bg-white p-4">
          <div className="min-w-0 flex-1">
            <p className="text-xs text-muted-fg">{t("selected")}</p>
            <p className="truncate text-sm font-medium text-cocoa-900" title={file.name}>
              {file.name}
            </p>
          </div>

          <span className="tabular text-xs text-muted-fg">
            {formatFileSize(file.size)}
          </span>

          <Button variant="ghost" size="icon-sm" onClick={onClear} aria-label={t("removeFile")}>
            <X aria-hidden />
          </Button>
        </div>
      ) : null}
    </div>
  );
}
