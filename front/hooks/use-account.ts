"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

import * as api from "@/lib/api/endpoints";
import { useIsAuthenticated } from "@/lib/auth/session-store";
import { queryKeys } from "@/lib/query-keys";

export function useActiveSessions() {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.sessions(),
    queryFn: ({ signal }) => api.listSessions(signal),
    enabled: authenticated,
  });
}

export function useNotifications() {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.notifications(),
    queryFn: ({ signal }) => api.listNotifications(signal),
    enabled: authenticated,
  });
}

export function useChangePassword() {
  const t = useTranslations("settings.password");

  return useMutation({
    mutationFn: (input: { currentPassword: string; newPassword: string }) =>
      api.changePassword({
        current_password: input.currentPassword,
        new_password: input.newPassword,
      }),
    onSuccess: () => toast.success(t("success")),
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sessionId: string) => api.revokeSession(sessionId),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions() }),
  });
}

export function useRevokeAllSessions() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.revokeAllSessions(),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions() }),
  });
}

export function useSetupMfa() {
  return useMutation({ mutationFn: () => api.setupMfa() });
}

export function useVerifyMfa() {
  return useMutation({ mutationFn: (code: string) => api.verifyMfa(code) });
}
