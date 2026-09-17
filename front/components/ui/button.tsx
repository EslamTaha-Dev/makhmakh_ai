import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  [
    "relative inline-flex items-center justify-center gap-2 whitespace-nowrap",
    "font-medium transition-[background-color,color,box-shadow,transform] duration-200",
    "disabled:pointer-events-none disabled:opacity-55",
    "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-500",
    "[&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        primary:
          "bg-brand-500 text-white shadow-brand hover:bg-brand-600 active:translate-y-px",
        secondary:
          "bg-cocoa-800 text-white hover:bg-cocoa-900 active:translate-y-px",
        outline:
          "border border-cocoa-800/15 bg-white text-cocoa-800 hover:border-brand-500/40 hover:bg-brand-50 active:translate-y-px",
        soft: "bg-brand-50 text-cocoa-800 hover:bg-brand-100 active:translate-y-px",
        ghost:
          "text-cocoa-800 hover:bg-cocoa-800/6 active:translate-y-px",
        danger:
          "bg-red-50 text-red-700 hover:bg-red-100 active:translate-y-px",
        link: "text-brand-600 underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-9 rounded-xl px-3.5 text-sm [&_svg]:size-4",
        md: "h-11 rounded-2xl px-5 text-sm [&_svg]:size-4",
        lg: "h-13 rounded-full px-7 text-base [&_svg]:size-5",
        icon: "size-10 rounded-xl [&_svg]:size-5",
        "icon-sm": "size-8 rounded-lg [&_svg]:size-4",
      },
      block: {
        true: "w-full",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export type ButtonProps = React.ComponentPropsWithRef<"button"> &
  VariantProps<typeof buttonVariants> & {
    loading?: boolean;
    loadingText?: string;
  };

export function Button({
  className,
  variant,
  size,
  block,
  loading = false,
  loadingText,
  disabled,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      type={props.type ?? "button"}
      className={cn(buttonVariants({ variant, size, block }), className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 aria-hidden className="animate-spin" />
          <span>{loadingText ?? children}</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
