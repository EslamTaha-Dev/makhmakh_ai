/** Response shapes mirroring the FastAPI schemas in `back/app/schemas`. */

export type Role =
  | "student"
  | "instructor"
  | "content_creator"
  | "support"
  | "admin"
  | "super_admin";

export type User = {
  id: string;
  name: string;
  email: string;
  role: Role | string;
  created_at: string;
};

export type RegisterResponse = User & {
  /** Only returned by a development backend, so the flow is testable without SMTP. */
  verification_token?: string | null;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type ForgotPasswordResponse = {
  status: string;
  reset_token?: string;
};

export type CourseVisibility = "public" | "private";

export type Course = {
  id: string;
  name: string;
  description: string | null;
  /** Decimal is serialised as a string by pydantic. */
  price: string;
  visibility: CourseVisibility;
  created_by: string;
  created_at: string;
};

export type MyCourse = {
  id: string;
  name: string;
  description: string | null;
  price: number;
  visibility: CourseVisibility;
  created_by: string;
  enrolled_at: string;
};

export type MaterialStatus = "pending" | "processing" | "completed" | "failed";

export type Material = {
  id: string;
  course_id: string;
  uploaded_by: string;
  file_name: string;
  file_type: string;
  storage_url: string | null;
  processing_status: MaterialStatus;
  error_message: string | null;
  uploaded_at: string;
};

export type ChatSource = {
  chunk_id: string | null;
  material_id: string;
  file_name: string;
  text: string;
  distance: number;
};

export type ChatResponse = {
  session_id: string;
  message_id: string;
  answer: string;
  sources: ChatSource[];
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | string;
  content: string;
  sources: ChatSource[] | null;
  created_at: string;
};

export type SessionInfo = {
  id: string;
  family_id: string;
  device_label: string | null;
  ip_address: string | null;
  created_at: string;
  expires_at: string;
};

export type ProgressRecord = {
  id: string;
  user_id: string;
  concept_id: string;
  status: string;
  completed_at: string | null;
};

export type CourseProgress = {
  course_id: string;
  lessons_completed: number;
  lessons_total: number;
  percent_complete: number;
};

export type GraphNode = {
  node_id: string;
  course_id: string;
  module: string | null;
  title: string;
  summary: string | null;
  difficulty: string | null;
  estimated_minutes: number | null;
  source_pages: string | null;
};

export type GraphEdge = {
  from_node: string;
  to_node: string;
  relation: string;
};

export type CourseGraph = {
  nodes: GraphNode[];
  edges: GraphEdge[];
};

export type ReadyNodes = {
  ready_nodes: string[];
  completed_nodes: string[];
};

export type NotificationItem = {
  id: string;
  user_id: string;
  type: string;
  payload: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
};

/** A message inside an `AIConversation` (the assistant's own history). */
export type AIMessageRecord = {
  id: string;
  conversation_id: string;
  interaction_id: string | null;
  role: "user" | "assistant" | string;
  content: string;
  created_at: string;
};

export type ConversationSummary = {
  id: string;
  student_id: string;
  course_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type Concept = {
  id: string;
  course_id: string;
  name: string;
  description: string | null;
  order_index: number;
  created_at: string;
};

export type Lesson = {
  id: string;
  concept_id: string;
  script_text: string | null;
  audio_url: string | null;
  video_url: string | null;
  duration_seconds: number | null;
  status: string;
  created_at: string;
};

export type LessonVideoStatus = {
  lesson_id: string;
  job_id?: string;
  status: string;
  progress_percent: number;
  video_url?: string | null;
  thumbnail_url?: string | null;
  error_message?: string | null;
  attempt_count?: number;
};

export type MfaSetup = {
  secret: string;
  provisioning_uri: string;
};

export type HealthStatus = {
  status: string;
  database?: string;
  queue?: string;
};

/** Cursor pagination envelope used by `GET /courses`. */
export type CursorPage<T> = {
  items: T[];
  nextCursor: string | null;
};
