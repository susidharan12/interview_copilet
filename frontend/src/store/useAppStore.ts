import { create } from "zustand";
import type {
  Session,
  Transcription,
  QuestionDetected,
  AnswerDone,
  Source,
  PipelineStage,
  AnswerMode,
  QuestionCategory,
} from "@/types";

interface PipelineStatus {
  stage: PipelineStage;
  message: string;
}

interface AppState {
  session: Session | null;
  sessionActive: boolean;
  mode: AnswerMode;
  pipelineStatus: PipelineStatus | null;
  transcript: Transcription[];
  currentQuestion: QuestionDetected | null;
  answerText: string;
  answerDone: AnswerDone | null;
  sources: Source[];
  isGenerating: boolean;
  showOverlay: boolean;
  settingsPanelOpen: boolean;
  history: Array<{ question: string; answer: string; category: QuestionCategory; timestamp: number }>;
  currentCode: string;
  error: string | null;

  setSession: (s: Session) => void;
  setMode: (m: AnswerMode) => void;
  addTranscription: (t: Transcription) => void;
  clearTranscript: () => void;
  setCurrentQuestion: (q: QuestionDetected | null) => void;
  setPipelineStatus: (ps: PipelineStatus | null) => void;
  appendAnswerToken: (token: string) => void;
  setAnswerDone: (a: AnswerDone) => void;
  setSources: (s: Source[]) => void;
  setIsGenerating: (g: boolean) => void;
  toggleOverlay: () => void;
  toggleSettings: () => void;
  clearAnswer: () => void;
  pushHistory: (item: { question: string; answer: string; category: QuestionCategory; timestamp: number }) => void;
  setCurrentCode: (code: string) => void;
  setError: (e: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  session: null,
  sessionActive: false,
  mode: "interview",
  pipelineStatus: null,
  transcript: [],
  currentQuestion: null,
  answerText: "",
  answerDone: null,
  sources: [],
  isGenerating: false,
  showOverlay: false,
  settingsPanelOpen: false,
  history: [],
  currentCode: "",
  error: null,

  setSession: (s) => set({ session: s, sessionActive: true }),
  setMode: (m) => set({ mode: m }),
  addTranscription: (t) => set((st) => ({ transcript: [...st.transcript, t].slice(-50) })),
  clearTranscript: () => set({ transcript: [] }),
  setCurrentQuestion: (q) => set({ currentQuestion: q }),
  setPipelineStatus: (ps) => set({ pipelineStatus: ps }),
  appendAnswerToken: (token) => set((st) => ({ answerText: st.answerText + token })),
  setAnswerDone: (a) =>
    set((st) => ({
      answerDone: a,
      isGenerating: false,
      answerText: a.full_text,
      history: [
        ...st.history,
        {
          question: st.currentQuestion?.text ?? "",
          answer: a.full_text,
          category: st.currentQuestion?.category ?? "unknown",
          timestamp: Date.now(),
        },
      ],
    })),
  setSources: (s) => set({ sources: s }),
  setIsGenerating: (g) => set({ isGenerating: g }),
  toggleOverlay: () => set((st) => ({ showOverlay: !st.showOverlay })),
  toggleSettings: () => set((st) => ({ settingsPanelOpen: !st.settingsPanelOpen })),
  clearAnswer: () => set({ answerText: "", answerDone: null, sources: [] }),
  pushHistory: (item) => set((st) => ({ history: [...st.history, item] })),
  setCurrentCode: (code) => set({ currentCode: code }),
  setError: (e) => set({ error: e }),
}));
