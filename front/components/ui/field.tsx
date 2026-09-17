import { AlertCircle } from "lucide-react";
import * as React from "react";

import { cn } from "@/lib/utils";

const controlClasses = [
  "w-full rounded-2xl border bg-white px-4 text-sm text-ink",
  "placeholder:text-muted-fg/70",
  "transition-[border-color,box-shadow] duration-200",
  "border-cocoa-800/15",
  "hover:border-cocoa-800/25",
  "focus:border-brand-500 focus:outline-none focus:ring-4 focus:ring-brand-500/12",
  "disabled:cursor-not-allowed disabled:bg-muted disabled:opacity-70",
  "aria-[invalid=true]:border-red-400 aria-[invalid=true]:focus:ring-red-500/12",
].join(" ");

export type FieldProps = {
  label: string;
  htmlFor?: string;
  error?: string;
  hint?: string;
  required?: boolean;
  className?: string;
  children: React.ReactNode;
};

export function Field({
  label,
  htmlFor,
  error,
  hint,
  required,
  className,
  children,
}: FieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <label
        htmlFor={htmlFor}
        className="block text-sm font-medium text-cocoa-900"
      >
        {label}
        {required ? (
          <span aria-hidden className="text-brand-500">
            {" "}
            *
          </span>
        ) : null}
      </label>

      {children}

      {error ? (
        <p className="flex items-start gap-1.5 text-xs text-red-600">
          <AlertCircle aria-hidden className="mt-0.5 size-3.5 shrink-0" />
          <span className="break-arabic">{error}</span>
        </p>
      ) : hint ? (
        <p className="text-xs text-muted-fg break-arabic">{hint}</p>
      ) : null}
    </div>
  );
}

export function Input({
  className,
  ...props
}: React.ComponentPropsWithRef<"input">) {
  return (
    <input
      className={cn(controlClasses, "h-12", className)}
      {...props}
    />
  );
}

export function Textarea({
  className,
  ...props
}: React.ComponentPropsWithRef<"textarea">) {
  return (
    <textarea
      className={cn(controlClasses, "min-h-28 resize-y py-3 leading-relaxed", className)}
      {...props}
    />
  );
}

export function Select({
  className,
  children,
  ...props
}: React.ComponentPropsWithRef<"select">) {
  return (
    <select
      className={cn(controlClasses, "h-12 pe-10 ps-4", className)}
      {...props}
    >
      {children}
    </select>
  );
}
