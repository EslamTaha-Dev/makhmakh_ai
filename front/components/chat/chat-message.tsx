"use client";

import { ChevronDown, Quote, Sparkles, User } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";

import { Badge } from "@/components/ui/badge";
import type { ChatSource } from "@/lib/api/types";
import { cn } from "@/lib/utils";

export type ChatTurn = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  /** Set when the turn failed, so the UI can offer a retry. */
  failed?: boolean;
};

function SourceList({ sources }: { sources: ChatSource[] }) {
  const t = useTranslations("chat");
  const [open, setOpen] = React.useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-3 rounded-2xl border border-cocoa-800/10 bg-white/70">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 px-3.5 py-2.5 text-start"
      >
        <span className="inline-flex items-center gap-2 text-xs font-medium text-cocoa-800">
          <Quote aria-hidden className="size-3.5 text-brand-500" />
          {t("sources")}
          <Badge tone="neutral">
            {t("sourcesCount", { count: sources.length })}
          </Badge>
        </span>

        <ChevronDown
          aria-hidden
          className={cn(
            "size-4 shrink-0 text-muted-fg transition duration-300",
            open && "rotate-180",
          )}
        />
      </button>

      {open ? (
        <ul className="space-y-2 border-t border-cocoa-800/8 px-3.5 py-3 motion-safe:animate-in motion-safe:fade-in">
          {sources.map((source, index) => (
            <li
              key={`${source.material_id}-${source.chunk_id ?? index}`}
              className="rounded-xl bg-muted/70 p-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="truncate text-xs font-medium text-cocoa-900" dir="auto">
                  {t("sourceFrom", { name: source.file_name })}
                </p>

                <span className="tabular text-[11px] text-muted-fg">
                  {t("matchScore")}: {(1 - source.distance).toFixed(2)}
                </span>
              </div>

              <p
                className="mt-1.5 line-clamp-4 text-xs leading-relaxed text-muted-fg break-arabic"
                dir="auto"
              >
                {source.text}
              </p>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function ChatMessage({ turn }: { turn: ChatTurn }) {
  const t = useTranslations("chat");
  const isUser = turn.role === "user";

  return (
    <li
      className={cn(
        "flex gap-3 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1",
        isUser ? "flex-row-reverse" : "",
      )}
    >
      <span
        className={cn(
          "flex size-9 shrink-0 items-center justify-center rounded-xl text-xs font-medium",
          isUser
            ? "bg-cocoa-800 text-white"
            : "brand-gradient-surface text-white",
        )}
        aria-hidden
      >
        {isUser ? <User className="size-4" /> : <Sparkles className="size-4" />}
      </span>

      <div className={cn("min-w-0 max-w-[85%]", isUser ? "text-end" : "")}>
        <p className="mb-1 text-[11px] font-medium text-muted-fg">
          {isUser ? t("youName") : t("assistantName")}
        </p>

        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap break-arabic",
            isUser
              ? "bg-cocoa-800 text-white"
              : turn.failed
                ? "border border-red-200 bg-red-50 text-red-900"
                : "border border-cocoa-800/10 bg-white text-cocoa-900 shadow-soft",
          )}
          dir="auto"
        >
          {turn.content}
        </div>

        {!isUser && turn.sources?.length ? (
          <SourceList sources={turn.sources} />
        ) : null}
      </div>
    </li>
  );
}

export function ChatThinking() {
  const t = useTranslations("chat");

  return (
    <li className="flex gap-3" aria-live="polite">
      <span
        aria-hidden
        className="flex size-9 shrink-0 items-center justify-center rounded-xl brand-gradient-surface text-white"
      >
        <Sparkles className="size-4" />
      </span>

      <div className="min-w-0">
        <p className="mb-1 text-[11px] font-medium text-muted-fg">
          {t("assistantName")}
        </p>

        <div className="inline-flex items-center gap-1.5 rounded-2xl border border-cocoa-800/10 bg-white px-4 py-3.5 shadow-soft">
          <span className="sr-only">{t("sending")}</span>
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              aria-hidden
              style={{ animationDelay: `${delay}ms` }}
              className="size-2 animate-bounce rounded-full bg-brand-400"
            />
          ))}
        </div>
      </div>
    </li>
  );
}
