"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import * as React from "react";

import * as api from "@/lib/api/endpoints";
import type { Material } from "@/lib/api/types";
import { useIsAuthenticated } from "@/lib/auth/session-store";
import { queryKeys } from "@/lib/query-keys";

export function useMyMaterials() {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.myMaterials(),
    queryFn: ({ signal }) => api.listMyMaterials(signal),
    enabled: authenticated,
  });
}

export function useCourseMaterials(courseId: string) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.courseMaterials(courseId),
    queryFn: ({ signal }) => api.listCourseMaterials(courseId, signal),
    enabled: authenticated && Boolean(courseId),
  });
}

export function useUploadMaterial(courseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (file: File) => api.uploadMaterial(courseId, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.courseMaterials(courseId),
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.myMaterials() });
    },
  });
}

/** Polls a material until processing settles, then refreshes the derived views. */
export function useMaterialProcessing(materialId: string | null) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.material(materialId ?? "none"),
    queryFn: ({ signal }) => api.getMaterial(materialId as string, signal),
    enabled: Boolean(materialId),
    refetchInterval: (queryResult) => {
      const status = (queryResult.state.data as Material | undefined)
        ?.processing_status;

      if (!status) return 2000;
      return status === "pending" || status === "processing" ? 2500 : false;
    },
  });

  const status = query.data?.processing_status;

  React.useEffect(() => {
    if (status !== "completed") return;

    // Concepts, graph and progress all change once processing finishes.
    void queryClient.invalidateQueries({ queryKey: ["progress"] });
    void queryClient.invalidateQueries({ queryKey: ["graph"] });
    if (query.data?.course_id) {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.courseMaterials(query.data.course_id),
      });
    }
    void queryClient.invalidateQueries({ queryKey: queryKeys.myMaterials() });
  }, [status, query.data?.course_id, queryClient]);

  return query;
}
