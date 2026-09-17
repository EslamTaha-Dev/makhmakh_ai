export const queryKeys = {
  courseCatalog: (cursor?: string | null) =>
    ["courses", "catalog", cursor ?? "first"] as const,
  course: (courseId: string) => ["courses", "detail", courseId] as const,
  myCourses: () => ["courses", "mine"] as const,
  myMaterials: () => ["materials", "mine"] as const,
  courseMaterials: (courseId: string) =>
    ["materials", "course", courseId] as const,
  material: (materialId: string) => ["materials", "detail", materialId] as const,
  courseConcepts: (courseId: string) => ["concepts", courseId] as const,
  courseGraph: (courseId: string) => ["graph", courseId] as const,
  readyNodes: (courseId: string) => ["graph", courseId, "ready"] as const,
  myProgress: () => ["progress", "mine"] as const,
  courseProgress: (courseId: string) =>
    ["progress", "course", courseId] as const,
  conversations: () => ["conversations"] as const,
  chatMessages: (sessionId: string) =>
    ["chat", "session", sessionId] as const,
  sessions: () => ["auth", "sessions"] as const,
  notifications: () => ["notifications"] as const,
  health: () => ["health"] as const,
};
