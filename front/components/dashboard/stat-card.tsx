import type { ElementType } from "react";

import { Skeleton } from "@/components/ui/states";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  loading = false,
  className,
}: {
  label: string;
  value: number | string;
  hint?: string;
  icon: ElementType;
  loading?: boolean;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-cocoa-800/10 bg-white p-5 shadow-soft transition duration-300 hover:border-brand-500/25 hover:shadow-lift",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-fg break-arabic">{label}</p>
        <span className="flex size-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
          <Icon aria-hidden className="size-4.5" />
        </span>
      </div>

      {loading ? (
        <Skeleton className="mt-3 h-8 w-16" />
      ) : (
        <p className="tabular mt-2 font-display text-3xl text-cocoa-900">
          {value}
        </p>
      )}

      {hint ? (
        <p className="mt-1 text-xs text-muted-fg break-arabic">{hint}</p>
      ) : null}
    </div>
  );
}
