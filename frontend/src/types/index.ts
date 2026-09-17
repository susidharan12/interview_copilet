export type SessionStatus = "active" | "paused" | "ended";
export type AnswerMode = "quick" | "interview" | "senior" | "coding" | "scenario";
export type PipelineStage = "listening" | "transcribing" | "detecting" | "classifying" | "retrieving" | "thinking" | "validating" | "answering";
export type QuestionCategory =
  | "technical" | "coding" | "debugging" | "system_design" | "architecture"
  | "scenario" | "behavioral" | "project" | "resume" | "sql"
  | "follow_up" | "clarification" | "unknown";

export interface Session {
  id: string;
  status: SessionStatus;
  mode: string;
  started_at: string;
  turn_count: number;
}

export interface Transcription {
  text: string;
  confidence: number;
  speaker?: string;
  is_final: boolean;
  timestamp: number;
}

export interface QuestionDetected {
  question_id?: string;
  text: string;
  category: QuestionCategory;
  classification: ClassificationResult;
  confidence: number;
}

export interface ClassificationResult {
  category: QuestionCategory;
  technology: string | null;
  difficulty: "easy" | "medium" | "hard" | null;
  requires_retrieval: boolean;
  requires_reasoning: boolean;
  requires_code_execution: boolean;
  requires_screen_context: boolean;
  confidence: number;
}

export interface Source {
  chunk_id: string;
  document_id: string;
  content_preview: string;
  score: number;
}

export interface AnswerDelta {
  answer_id: string;
  token: string;
  mode: AnswerMode;
}

export interface AnswerDone {
  answer_id: string;
  full_text: string;
  mode: AnswerMode;
  sources: Source[];
  validation: Validation | null;
  latency_ms: number;
}

export interface Validation {
  passed: boolean;
  confidence: number;
  issues: string[];
}

export interface PipelineStatusEvent {
  stage: PipelineStage;
  message: string;
}

export interface Profile {
  user_id: string;
  name: string;
  resume_summary: string | null;
  skills: string[];
  experience_years: number | null;
  target_role: string | null;
}

export interface WsClientEvent {
  type: string;
  payload: Record<string, unknown>;
  request_id?: string;
}

export interface WsServerEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp: number;
}
