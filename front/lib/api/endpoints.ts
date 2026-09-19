import { apiRequest, apiRequestWithMeta } from "./client";
import type {
  AIMessageRecord,
  ChatMessage,
  ChatResponse,
  Concept,
  ConversationSummary,
  Course,
  CourseGraph,
  CourseProgress,
  CursorPage,
  HealthStatus,
  Lesson,
  LessonVideoStatus,
  Material,
  MfaSetup,
  MyCourse,
  NotificationItem,
  ProgressRecord,
  ReadyNodes,
  SessionInfo,
  TokenResponse,
  User,
} from "./types";

/* -------------------------------------------------------------------------- */
/* Auth                                                                        */
/* -------------------------------------------------------------------------- */

export function register(input: { name: string; email: string; password: string }) {
  return apiRequest<User>("/auth/register", {
    method: "POST",
    body: input,
    auth: false,
  });
}

export function login(input: { email: string; password: string }) {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: input,
    auth: false,
  });
}

export function getMe(signal?: AbortSignal) {
  return apiRequest<User>("/auth/me", { signal });
}

export function logout() {
  return apiRequest<{ message: string }>("/auth/logout", { method: "POST" });
}

export function changePassword(input: {
  current_password: string;
  new_password: string;
}) {
  return apiRequest<{ status: string }>("/auth/change-password", {
    method: "POST",
    body: input,
  });
}

export function listSessions(signal?: AbortSignal) {
  return apiRequest<SessionInfo[]>("/auth/sessions", { signal });
}

export function revokeSession(sessionId: string) {
  return apiRequest<{ status: string }>(`/auth/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export function revokeAllSessions() {
  return apiRequest<{ status: string }>("/auth/sessions", { method: "DELETE" });
}

export function setupMfa() {
  return apiRequest<MfaSetup>("/auth/mfa/setup", { method: "POST" });
}

export function verifyMfa(code: string) {
  return apiRequest<{ status: string }>("/auth/mfa/verify", {
    method: "POST",
    query: { code },
  });
}

/* -------------------------------------------------------------------------- */
/* Courses                                                                     */
/* -------------------------------------------------------------------------- */

export function listCourses(params: {
  cursor?: string | null;
  limit?: number;
  signal?: AbortSignal;
}): Promise<CursorPage<Course>> {
  return apiRequestWithMeta<Course[]>("/courses", {
    query: { cursor: params.cursor, limit: params.limit ?? 24 },
    signal: params.signal,
  }).then(({ data, nextCursor }) => ({ items: data, nextCursor }));
}

export function getCourse(courseId: string, signal?: AbortSignal) {
  return apiRequest<Course>(`/courses/${courseId}`, { signal });
}

export function createCourse(input: {
  name: string;
  description?: string | null;
}) {
  return apiRequest<Course>("/courses", {
    method: "POST",
    body: {
      name: input.name,
      description: input.description ?? null,
    },
  });
}

export function listMyCourses(signal?: AbortSignal) {
  return apiRequest<MyCourse[]>("/users/me/courses", { signal });
}

export function enrollInCourse(courseId: string) {
  return apiRequest<{ student_id: string; course_id: string; source: string }>(
    `/courses/${courseId}/enroll`,
    { method: "POST" },
  );
}

export function getMyCourseProgress(courseId: string, signal?: AbortSignal) {
  return apiRequest<CourseProgress>(`/users/me/courses/${courseId}/progress`, {
    signal,
  });
}

/* -------------------------------------------------------------------------- */
/* Materials                                                                   */
/* -------------------------------------------------------------------------- */

export function listCourseMaterials(courseId: string, signal?: AbortSignal) {
  return apiRequest<Material[]>(`/courses/${courseId}/materials`, { signal });
}

export function listMyMaterials(signal?: AbortSignal) {
  return apiRequest<Material[]>("/users/me/materials", { signal });
}

export function getMaterial(materialId: string, signal?: AbortSignal) {
  return apiRequest<Material>(`/courses/materials/${materialId}`, { signal });
}

export function uploadMaterial(
  courseId: string,
  file: File,
  options: { signal?: AbortSignal } = {},
) {
  const form = new FormData();
  form.append("file", file);

  return apiRequest<Material>(`/courses/${courseId}/materials`, {
    method: "POST",
    form,
    signal: options.signal,
  });
}

/* -------------------------------------------------------------------------- */
/* Knowledge graph, concepts, progress, lessons                                */
/* -------------------------------------------------------------------------- */

export function getCourseGraph(courseId: string, signal?: AbortSignal) {
  return apiRequest<CourseGraph>(`/courses/${courseId}/graph`, { signal });
}

export function buildCourseGraph(courseId: string) {
  return apiRequest<unknown>(`/courses/${courseId}/graph/build`, {
    method: "POST",
  });
}

export function getReadyNodes(courseId: string, signal?: AbortSignal) {
  return apiRequest<ReadyNodes>(`/courses/${courseId}/graph/ready`, { signal });
}

export function listCourseConcepts(courseId: string, signal?: AbortSignal) {
  return apiRequest<Concept[]>(`/courses/${courseId}/concepts`, { signal });
}

export function getConcept(conceptId: string, signal?: AbortSignal) {
  return apiRequest<Concept>(`/concepts/${conceptId}`, { signal });
}

export function completeConcept(conceptId: string) {
  return apiRequest<ProgressRecord>(`/concepts/${conceptId}/progress/complete`, {
    method: "POST",
  });
}

export function listMyProgress(signal?: AbortSignal) {
  return apiRequest<ProgressRecord[]>("/users/me/progress", { signal });
}

export function getLesson(lessonId: string, signal?: AbortSignal) {
  return apiRequest<Lesson>(`/lessons/${lessonId}`, { signal });
}

export function getLessonVideoStatus(lessonId: string, signal?: AbortSignal) {
  return apiRequest<LessonVideoStatus>(`/lessons/${lessonId}/video/status`, {
    signal,
  });
}

export function updateLessonProgress(
  lessonId: string,
  input: { status: string; videoWatchedSeconds?: number },
) {
  return apiRequest<{
    lesson_id: string;
    status: string;
    video_watched_seconds: number;
  }>(`/lessons/${lessonId}/progress`, {
    method: "POST",
    query: {
      status: input.status,
      video_watched_seconds: input.videoWatchedSeconds ?? 0,
    },
  });
}

/* -------------------------------------------------------------------------- */
/* Chat                                                                        */
/* -------------------------------------------------------------------------- */

export function sendChatMessage(
  courseId: string,
  input: { message: string; sessionId?: string | null; nodeId?: string | null },
  signal?: AbortSignal,
) {
  return apiRequest<ChatResponse>(`/courses/${courseId}/chat`, {
    method: "POST",
    body: {
      message: input.message,
      session_id: input.sessionId ?? null,
      node_id: input.nodeId ?? null,
    },
    signal,
  });
}

export function getChatMessages(sessionId: string, signal?: AbortSignal) {
  return apiRequest<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`, {
    signal,
  });
}

export function listConversations(signal?: AbortSignal) {
  return apiRequest<ConversationSummary[]>("/users/me/conversations", { signal });
}

export function getConversationMessages(
  conversationId: string,
  signal?: AbortSignal,
) {
  return apiRequest<AIMessageRecord[]>(
    `/conversations/${conversationId}/messages`,
    { signal },
  );
}

/* -------------------------------------------------------------------------- */
/* Notifications + health                                                      */
/* -------------------------------------------------------------------------- */

export function listNotifications(signal?: AbortSignal) {
  return apiRequest<NotificationItem[]>("/users/me/notifications", { signal });
}

export function markNotificationRead(notificationId: string) {
  return apiRequest<{ status: string }>(
    `/notifications/${notificationId}/read`,
    { method: "POST" },
  );
}

export function checkHealth(signal?: AbortSignal) {
  return apiRequest<HealthStatus>("/health", { auth: false, signal });
}
