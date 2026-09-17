import * as React from "react";

import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: React.ComponentPropsWithRef<"div">) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-cocoa-800/10 bg-white shadow-soft",
        className,
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  ...props
}: React.ComponentPropsWithRef<"div">) {
  return (
    <div
      className={cn("flex flex-wrap items-start justify-between gap-4 p-6", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  as: Tag = "h3",
  ...props
}: React.ComponentPropsWithRef<"h3"> & { as?: React.ElementType }) {
  return (
    <Tag
      className={cn(
        "font-display text-lg text-cocoa-900 sm:text-xl",
        className,
      )}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.ComponentPropsWithRef<"p">) {
  return (
    <p
      className={cn("text-sm text-muted-fg break-arabic", className)}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.ComponentPropsWithRef<"div">) {
  return <div className={cn("px-6 pb-6", className)} {...props} />;
}

export function CardFooter({
  className,
  ...props
}: React.ComponentPropsWithRef<"div">) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 border-t border-cocoa-800/8 px-6 py-4",
        className,
      )}
      {...props}
    />
  );
}
