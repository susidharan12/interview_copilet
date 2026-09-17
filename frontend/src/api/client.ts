import type { Profile, Session, AnswerMode } from "@/types";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}/api/v1${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const apiClient = {
  createSession: (jobProfileId?: string, mode = "interview", answerMode: AnswerMode = "interview") =>
    api<Session>("/sessions", {
      method: "POST",
      body: JSON.stringify({ job_profile_id: jobProfileId, mode, settings: { answer_mode: answerMode } }),
    }),

  getSession: (id: string) => api<Session>(`/sessions/${id}`),

  endSession: (id: string) =>
    api<Session>(`/sessions/${id}`, { method: "PATCH", body: JSON.stringify({ status: "ended" }) }),

  getProfile: () => api<Profile>("/profile"),

  updateProfile: (data: Partial<Profile>) =>
    api<Profile>("/profile", { method: "PUT", body: JSON.stringify(data) }),

  uploadDocument: async (file: File, documentType: string, tags: string[]) => {
    const form = new FormData();
    form.append("file", file);
    form.append("document_type", documentType);
    form.append("tags", tags.join(","));
    return api<{ id: string; status: string }>("/documents", { method: "POST", body: form });
  },

  search: (query: string, topK = 10) =>
    api<{ results: unknown[] }[]>("/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    }),

  classifyQuestion: (question: string) =>
    api<{ category: string; technology: string | null; difficulty: string | null }>(
      "/questions/classify",
      { method: "POST", body: JSON.stringify({ question_text: question }) },
    ),

  health: () => fetch(`${BASE}/health`).then((r) => r.json()),
};
