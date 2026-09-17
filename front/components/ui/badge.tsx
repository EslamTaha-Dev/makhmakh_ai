import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium [&_svg]:size-3.5",
  {
    variants: {
      tone: {
        brand: "bg-brand-500/12 text-brand-700",
        cocoa: "bg-cocoa-800/10 text-cocoa-900",
        yellow: "bg-brand-300/25 text-cocoa-900",
        neutral: "bg-muted text-muted-fg",
        success: "bg-emerald-50 text-emerald-700",
        danger: "bg-red-50 text-red-700",
        outline: "border border-cocoa-800/15 text-cocoa-800",
      },
    },
    defaultVariants: { tone: "neutral" },
  },
);

export type BadgeProps = React.ComponentPropsWithRef<"span"> &
  VariantProps<typeof badgeVariants>;

export function Badge({ className, tone, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ tone }), className)} {...props} />;
}
