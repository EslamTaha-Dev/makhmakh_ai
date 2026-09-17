import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const tones = {
  info: {
    wrapper: "border-brand-500/20 bg-brand-50 text-cocoa-900",
    icon: <Info aria-hidden className="size-4 text-brand-600" />,
  },
  success: {
    wrapper: "border-emerald-200 bg-emerald-50 text-emerald-900",
    icon: <CheckCircle2 aria-hidden className="size-4 text-emerald-600" />,
  },
  warning: {
    wrapper: "border-brand-300/50 bg-brand-100/50 text-cocoa-900",
    icon: <AlertTriangle aria-hidden className="size-4 text-brand-600" />,
  },
  error: {
    wrapper: "border-red-200 bg-red-50 text-red-900",
    icon: <XCircle aria-hidden className="size-4 text-red-600" />,
  },
} as const;

export type AlertProps = {
  tone?: keyof typeof tones;
  title?: string;
  children?: React.ReactNode;
  className?: string;
};

export function Alert({ tone = "info", title, children, className }: AlertProps) {
  const styles = tones[tone];

  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "flex items-start gap-3 rounded-2xl border px-4 py-3 text-sm",
        styles.wrapper,
        className,
      )}
    >
      <span className="mt-0.5 shrink-0">{styles.icon}</span>

      <div className="min-w-0 space-y-0.5">
        {title ? (
          <p className="font-medium break-arabic">{title}</p>
        ) : null}
        {children ? (
          <div className="break-arabic text-[0.92em] opacity-90">{children}</div>
        ) : null}
      </div>
    </div>
  );
}
