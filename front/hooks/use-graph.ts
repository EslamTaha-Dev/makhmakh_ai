"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as api from "@/lib/api/endpoints";
import { useIsAuthenticated } from "@/lib/auth/session-store";
import { queryKeys } from "@/lib/query-keys";

export function useCourseConcepts(courseId: string) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.courseConcepts(courseId),
    queryFn: ({ signal }) => api.listCourseConcepts(courseId, signal),
    enabled: authenticated && Boolean(courseId),
  });
}

export function useCourseGraph(courseId: string) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.courseGraph(courseId),
    queryFn: ({ signal }) => api.getCourseGraph(courseId, signal),
    enabled: authenticated && Boolean(courseId),
  });
}

export function useReadyNodes(courseId: string) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.readyNodes(courseId),
    queryFn: ({ signal }) => api.getReadyNodes(courseId, signal),
    enabled: authenticated && Boolean(courseId),
  });
}

export function useBuildCourseGraph(courseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.buildCourseGraph(courseId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.courseConcepts(courseId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.courseGraph(courseId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.readyNodes(courseId),
      });
    },
  });
}
