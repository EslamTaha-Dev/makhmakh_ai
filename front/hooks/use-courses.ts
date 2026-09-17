"use client";

import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query";

import * as api from "@/lib/api/endpoints";
import type { Course, CursorPage, MyCourse } from "@/lib/api/types";
import { useIsAuthenticated } from "@/lib/auth/session-store";
import { queryKeys } from "@/lib/query-keys";

export function useMyCourses(
  options?: Omit<UseQueryOptions<MyCourse[]>, "queryKey" | "queryFn">,
) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.myCourses(),
    queryFn: ({ signal }) => api.listMyCourses(signal),
    enabled: authenticated,
    ...options,
  });
}

export function useCourseCatalog(cursor: string | null = null) {
  const authenticated = useIsAuthenticated();

  return useQuery<CursorPage<Course>>({
    queryKey: queryKeys.courseCatalog(cursor),
    queryFn: ({ signal }) =>
      api.listCourses({ cursor, limit: 24, signal }),
    enabled: authenticated,
  });
}

/** Catalog with cursor pagination collapsed into one list. */
export function useCourseCatalogInfinite() {
  const authenticated = useIsAuthenticated();

  return useInfiniteQuery({
    queryKey: queryKeys.courseCatalog("infinite"),
    initialPageParam: null as string | null,
    queryFn: ({ pageParam, signal }) =>
      api.listCourses({
        cursor: pageParam,
        limit: 24,
        signal,
      }),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    enabled: authenticated,
  });
}

export function useCourse(courseId: string) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.course(courseId),
    queryFn: ({ signal }) => api.getCourse(courseId, signal),
    enabled: authenticated && Boolean(courseId),
  });
}

export function useCourseProgress(courseId: string) {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.courseProgress(courseId),
    queryFn: ({ signal }) => api.getMyCourseProgress(courseId, signal),
    enabled: authenticated && Boolean(courseId),
  });
}

export function useMyProgress() {
  const authenticated = useIsAuthenticated();

  return useQuery({
    queryKey: queryKeys.myProgress(),
    queryFn: ({ signal }) => api.listMyProgress(signal),
    enabled: authenticated,
  });
}

export function useCreateCourse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      name: string;
      description?: string | null;
      price?: number;
    }) => api.createCourse(input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.myCourses() });
      void queryClient.invalidateQueries({ queryKey: ["courses", "catalog"] });
    },
  });
}

export function useEnrollInCourse() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (courseId: string) => api.enrollInCourse(courseId),
    onSuccess: (_data, courseId) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.myCourses() });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.courseProgress(courseId),
      });
    },
  });
}

export function useCompleteConcept(courseId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (conceptId: string) => api.completeConcept(conceptId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.myProgress() });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.courseProgress(courseId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.readyNodes(courseId),
      });
    },
  });
}
