"use client";

import { CheckCircle2, Clock, Loader2, XCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import type { ElementType } from "react";

import { Badge } from "@/components/ui/badge";
import type { MaterialStatus } from "@/lib/api/types";

const CONFIG: Record<
  MaterialStatus,
  { tone: "neutral" | "brand" | "success" | "danger"; icon: ElementType }
> = {
  pending: { tone: "neutral", icon: Clock },
  processing: { tone: "brand", icon: Loader2 },
  completed: { tone: "success", icon: CheckCircle2 },
  failed: { tone: "danger", icon: XCircle },
};

export function MaterialStatusBadge({ status }: { status: MaterialStatus }) {
  const t = useTranslations("status");
  const config = CONFIG[status] ?? CONFIG.pending;
  const Icon = config.icon;

  return (
    <Badge tone={config.tone}>
      <Icon
        aria-hidden
        className={status === "processing" ? "animate-spin" : undefined}
      />
      {t.has(status) ? t(status) : status}
    </Badge>
  );
}
