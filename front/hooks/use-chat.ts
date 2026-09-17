"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import * as api from "@/lib/api/endpoints";
import type { ChatResponse } from "@/lib/api/types";
import { useIsAuthenticated } from "@/lib/auth/session-store";
import { queryKeys } from "@/lib/query-keys";

export function useConversations() {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.conversations(),
    queryFn: ({ signal }) => api.listConversations(signal),
    enabled: authenticated,
  });
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ["conversations", conversationId, "messages"],
    queryFn: ({ signal }) =>
      api.getConversationMessages(conversationId as string, signal),
    enabled: Boolean(conversationId),
  });
}

export function useSendChatMessage(courseId: string) {
  const queryClient = useQueryClient();

  return useMutation<
    ChatResponse,
    Error,
    { message: string; sessionId?: string | null; nodeId?: string | null }
  >({
    mutationFn: (input) =>
      api.sendChatMessage(courseId, {
        message: input.message,
        sessionId: input.sessionId,
        nodeId: input.nodeId,
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations() }),
  });
}
