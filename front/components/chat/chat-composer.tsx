"use client";

import { Send } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { Button } from "@/components/ui/button";

export function ChatComposer({
  value,
  onChange,
  onSubmit,
  disabled = false,
  pending = false,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  pending?: boolean;
}) {
  const t = useTranslations("chat");
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Grow with the content up to a sensible ceiling.
  React.useEffect(() => {
    const node = textareaRef.current;
    if (!node) return;

    node.style.height = "auto";
    node.style.height = `${Math.min(node.scrollHeight, 200)}px`;
  }, [value]);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || pending || disabled) return;
    onSubmit();
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
      className="flex items-end gap-3 rounded-3xl border border-cocoa-800/12 bg-white p-3 shadow-soft transition focus-within:border-brand-500/40"
    >
      <label htmlFor="chat-input" className="sr-only">
        {t("placeholder")}
      </label>

      <textarea
        id="chat-input"
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            submit();
          }
        }}
        rows={1}
        maxLength={5000}
        disabled={disabled}
        placeholder={t("placeholder")}
        className="scrollbar-slim max-h-48 min-h-11 w-full resize-none border-0 bg-transparent px-2 py-2.5 text-sm leading-relaxed text-ink placeholder:text-muted-fg/70 focus:outline-none disabled:opacity-60"
      />

      <Button
        type="submit"
        size="icon"
        disabled={disabled || !value.trim()}
        loading={pending}
        aria-label={t("send")}
        className="shrink-0"
      >
        {pending ? null : <Send aria-hidden />}
      </Button>
    </form>
  );
}
