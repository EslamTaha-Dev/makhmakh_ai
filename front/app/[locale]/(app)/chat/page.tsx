"use client";

import { History, MessageSquareText, Plus, Sparkles } from "lucide-react";
import { useLocale, useTranslations } from "next-intl";
import * as React from "react";

import { ChatComposer } from "@/components/chat/chat-composer";
import { ChatMessage, ChatThinking, type ChatTurn } from "@/components/chat/chat-message";
import { CreateSpaceDialog } from "@/components/subjects/create-space-dialog";
import { Alert } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/field";
import { Modal } from "@/components/ui/modal";
import { EmptyState, ErrorState, Skeleton } from "@/components/ui/states";
import { useApiErrorMessage } from "@/hooks/use-api-error";
import {
  useConversationMessages,
  useConversations,
  useSendChatMessage,
} from "@/hooks/use-chat";
import { useMyCourses } from "@/hooks/use-courses";
import { useQueryParam } from "@/hooks/use-query-param";
import { ApiError } from "@/lib/api/client";
import type { ChatFailureResponse, ConversationSummary } from "@/lib/api/types";
import { formatRelativeTime } from "@/lib/format";
import { cn } from "@/lib/utils";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getSessionIdFromError(error: unknown): string | null {
  if (!(error instanceof ApiError)) return null;
  if (!error.payload || typeof error.payload !== "object") return null;

  const detail = (error.payload as Partial<ChatFailureResponse>).detail;
  const sessionId = detail?.session_id;
  return typeof sessionId === "string" && sessionId ? sessionId : null;
}

export default function ChatPage() {
  const t = useTranslations("chat");
  const tCommon = useTranslations("common");
  const locale = useLocale();
  const describeError = useApiErrorMessage();

  const { value: spaceParam } = useQueryParam("space");
  const myCourses = useMyCourses();
  const conversations = useConversations();

  const [courseId, setCourseId] = React.useState("");
  const [turns, setTurns] = React.useState<ChatTurn[]>([]);
  const [draft, setDraft] = React.useState("");
  const [sessionId, setSessionId] = React.useState<string | null>(null);
  const [openConversation, setOpenConversation] =
    React.useState<ConversationSummary | null>(null);

  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (courseId || !myCourses.data?.length) return;

    const requested = spaceParam
      ? myCourses.data.find((course) => course.id === spaceParam)
      : undefined;

    setCourseId(requested?.id ?? myCourses.data[0].id);
  }, [spaceParam, myCourses.data, courseId]);

  const sendMessage = useSendChatMessage(courseId || "none");
  const history = useConversationMessages(openConversation?.id ?? null);

  const suggestions = React.useMemo(
    () => (t.raw("suggestions.items") as string[]) ?? [],
    [t],
  );

  React.useEffect(() => {
    const node = scrollRef.current;
    if (!node) return;
    node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
  }, [turns, sendMessage.isPending]);

  // A different space means a different corpus, so start fresh.
  const handleCourseChange = (value: string) => {
    setCourseId(value);
    setTurns([]);
    setSessionId(null);
  };

  const handleSend = async (override?: string) => {
    const message = (override ?? draft).trim();
    if (!message || !courseId || sendMessage.isPending) return;

    setTurns((previous) => [
      ...previous,
      { id: newId(), role: "user", content: message },
    ]);
    setDraft("");

    try {
      const response = await sendMessage.mutateAsync({
        message,
        sessionId,
      });

      setSessionId(response.session_id);
      setTurns((previous) => [
        ...previous,
        {
          id: response.message_id,
          role: "assistant",
          content: response.answer,
          sources: response.sources,
        },
      ]);
    } catch (error) {
      const failedSessionId = getSessionIdFromError(error);

      if (failedSessionId) {
        setSessionId(failedSessionId);
      }

      setTurns((previous) => [
        ...previous,
        {
          id: newId(),
          role: "assistant",
          content: describeError(error, "chat"),
          failed: true,
        },
      ]);
    }
  };

  if (myCourses.isPending) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (myCourses.isError) {
    return (
      <ErrorState
        title={tCommon("offlineHint")}
        onRetry={() => void myCourses.refetch()}
        retryLabel={tCommon("retry")}
      />
    );
  }

  if (!myCourses.data.length) {
    return (
      <div className="space-y-6">
        <header className="space-y-1.5">
          <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
            {t("title")}
          </h1>
          <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
        </header>

        <EmptyState
          icon={<Sparkles aria-hidden />}
          title={t("noSpace")}
          body={t("noSpaceCta")}
          action={
            <CreateSpaceDialog
              navigateOnCreate
              trigger={
                <span className={cn(buttonVariants({ size: "md" }), "cursor-pointer")}>
                  {t("noSpaceCta")}
                </span>
              }
            />
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="space-y-1.5">
        <h1 className="font-display text-2xl text-cocoa-900 sm:text-3xl">
          {t("title")}
        </h1>
        <p className="text-sm text-muted-fg break-arabic">{t("subtitle")}</p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1.65fr_0.85fr] lg:items-start">
        <Card className="flex h-[calc(100dvh-16rem)] min-h-125 flex-col overflow-hidden">
          <div className="flex flex-wrap items-center gap-3 border-b border-cocoa-800/8 p-4">
            <label htmlFor="chat-space" className="text-xs font-medium text-muted-fg">
              {t("space")}
            </label>

            <Select
              id="chat-space"
              value={courseId}
              onChange={(event) => handleCourseChange(event.target.value)}
              className="h-10 max-w-64 flex-1"
            >
              {myCourses.data.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.name}
                </option>
              ))}
            </Select>

            <Button
              variant="ghost"
              size="sm"
              className="ms-auto"
              onClick={() => {
                setTurns([]);
                setSessionId(null);
              }}
              disabled={!turns.length}
            >
              <Plus aria-hidden />
              {t("newChat")}
            </Button>
          </div>

          <div
            ref={scrollRef}
            className="scrollbar-slim flex-1 overflow-y-auto px-4 py-5"
          >
            {turns.length === 0 && !sendMessage.isPending ? (
              <div className="flex h-full flex-col items-center justify-center gap-6 px-4 text-center">
                <span className="flex size-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
                  <MessageSquareText aria-hidden className="size-7" />
                </span>

                <div className="space-y-1.5">
                  <p className="font-display text-lg text-cocoa-900">
                    {t("emptyTitle")}
                  </p>
                  <p className="mx-auto max-w-sm text-sm text-muted-fg break-arabic">
                    {t("emptyBody")}
                  </p>
                </div>

                <ul className="flex w-full max-w-md flex-col gap-2">
                  {suggestions.map((suggestion) => (
                    <li key={suggestion}>
                      <button
                        type="button"
                        onClick={() => void handleSend(suggestion)}
                        className="w-full rounded-2xl border border-cocoa-800/10 bg-white px-4 py-2.5 text-start text-sm text-cocoa-800 transition hover:border-brand-500/30 hover:bg-brand-50/50 break-arabic"
                      >
                        {suggestion}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <ul className="space-y-5">
                {turns.map((turn) => (
                  <ChatMessage key={turn.id} turn={turn} />
                ))}

                {sendMessage.isPending ? <ChatThinking /> : null}
              </ul>
            )}
          </div>

          <div className="border-t border-cocoa-800/8 p-4">
            <ChatComposer
              value={draft}
              onChange={setDraft}
              onSubmit={() => void handleSend()}
              pending={sendMessage.isPending}
            />

            {sendMessage.isError ? (
              <Alert tone="error" className="mt-3">
                {describeError(sendMessage.error, "chat")}
              </Alert>
            ) : null}
          </div>
        </Card>

        <Card className="p-5">
          <CardTitle as="h2" className="flex items-center gap-2 text-base">
            <History aria-hidden className="size-4 text-brand-500" />
            {t("history.title")}
          </CardTitle>

          <div className="mt-4">
            {conversations.isPending ? (
              <div className="space-y-2">
                {[0, 1, 2].map((key) => (
                  <Skeleton key={key} className="h-14" />
                ))}
              </div>
            ) : conversations.isError ? (
              <p className="text-xs text-muted-fg">{tCommon("offlineHint")}</p>
            ) : conversations.data.length === 0 ? (
              <p className="text-sm text-muted-fg break-arabic">
                {t("history.empty")}
              </p>
            ) : (
              <ul className="space-y-2">
                {conversations.data.slice(0, 8).map((conversation) => (
                  <li key={conversation.id}>
                    <button
                      type="button"
                      onClick={() => setOpenConversation(conversation)}
                      className="w-full rounded-2xl border border-cocoa-800/10 bg-white px-3.5 py-3 text-start transition hover:border-brand-500/30 hover:bg-brand-50/50"
                    >
                      <p className="line-clamp-2 text-xs font-medium text-cocoa-900 break-arabic">
                        {conversation.title || t("emptyTitle")}
                      </p>
                      <p className="mt-0.5 text-[11px] text-muted-fg">
                        {formatRelativeTime(conversation.updated_at, locale)}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>
      </div>

      <Modal
        open={Boolean(openConversation)}
        onClose={() => setOpenConversation(null)}
        title={openConversation?.title || t("history.title")}
        className="max-w-2xl"
      >
        {history.isPending ? (
          <div className="space-y-3">
            {[0, 1, 2].map((key) => (
              <Skeleton key={key} className="h-14" />
            ))}
          </div>
        ) : history.isError ? (
          <Alert tone="error">{tCommon("offlineHint")}</Alert>
        ) : history.data.length === 0 ? (
          <p className="text-sm text-muted-fg">{t("history.empty")}</p>
        ) : (
          <ul className="scrollbar-slim max-h-96 space-y-4 overflow-y-auto pe-1">
            {history.data.map((message) => (
              <li
                key={message.id}
                className={cn(
                  "rounded-2xl p-3.5 text-sm leading-relaxed",
                  message.role === "user"
                    ? "bg-cocoa-800 text-white"
                    : "border border-cocoa-800/10 bg-muted/50 text-cocoa-900",
                )}
                dir="auto"
              >
                {message.content}
              </li>
            ))}
          </ul>
        )}
      </Modal>
    </div>
  );
}
