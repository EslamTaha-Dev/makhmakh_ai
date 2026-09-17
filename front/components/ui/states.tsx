import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Spinner({
  className,
  label,
}: {
  className?: string;
  label?: string;
}) {
  return (
    <span className="inline-flex items-center gap-2" role="status">
      <Loader2 aria-hidden className={cn("size-4 animate-spin", className)} />
      {label ? <span className="text-sm text-muted-fg">{label}</span> : null}
    </span>
  );
}

export function Skeleton({
  className,
  ...props
}: React.ComponentPropsWithRef<"div">) {
  return (
    <div
      aria-hidden
      className={cn(
        "relative overflow-hidden rounded-2xl bg-muted",
        "after:absolute after:inset-0 after:animate-[brand-shimmer_1.6s_infinite]",
        "after:bg-gradient-to-r after:from-transparent after:via-white/70 after:to-transparent",
        className,
      )}
      {...props}
    />
  );
}

export function EmptyState({
  icon,
  title,
  body,
  action,
  className,
}: {
  icon?: React.ReactNode;
  title: string;
  body?: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-3xl border border-dashed border-cocoa-800/15 bg-white/60 px-6 py-14 text-center",
        className,
      )}
    >
      {icon ? (
        <span className="flex size-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-500 [&_svg]:size-7">
          {icon}
        </span>
      ) : null}

      <div className="space-y-1.5">
        <p className="font-display text-lg text-cocoa-900 break-arabic">{title}</p>
        {body ? (
          <p className="mx-auto max-w-md text-sm text-muted-fg break-arabic">
            {body}
          </p>
        ) : null}
      </div>

      {action}
    </div>
  );
}

export function ErrorState({
  title,
  body,
  onRetry,
  retryLabel,
  className,
  children,
}: {
  title: string;
  body?: string;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-3xl border border-red-200/70 bg-red-50/50 px-6 py-12 text-center",
        className,
      )}
    >
      <span className="flex size-12 items-center justify-center rounded-2xl bg-red-100 text-red-600">
        <AlertTriangle aria-hidden className="size-6" />
      </span>

      <div className="space-y-1.5">
        <p className="font-display text-lg text-cocoa-900 break-arabic">
          {title}
        </p>
        {body ? (
          <p className="mx-auto max-w-md text-sm text-muted-fg break-arabic">
            {body}
          </p>
        ) : null}
      </div>

      {children}

      {onRetry ? (
        <Button variant="outline" onClick={onRetry}>
          <RefreshCw aria-hidden />
          {retryLabel}
        </Button>
      ) : null}
    </div>
  );
}
