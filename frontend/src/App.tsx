import React, { useEffect, useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import { apiClient } from "@/api/client";
import { useInterviewSocket, useMicCapture } from "@/hooks/useInterviewSocket";
import type { AnswerMode } from "@/types";
import { QuestionPanel } from "@/components/QuestionPanel";
import { AnswerPanel } from "@/components/AnswerPanel";
import { LiveTranscript } from "@/components/LiveTranscript";
import { SettingsPanel } from "@/components/SettingsPanel";

const MODES: AnswerMode[] = ["quick", "interview", "senior", "coding", "scenario"];

const STAGE_ICONS: Record<string, string> = {
  listening: "🎤",
  transcribing: "📝",
  detecting: "🔍",
  classifying: "🏷️",
  retrieving: "📚",
  thinking: "🧠",
  validating: "✅",
  answering: "💬",
};

const App: React.FC = () => {
  const {
    session, setSession, mode, setMode, pipelineStatus,
    showOverlay, toggleOverlay, clearAnswer, isGenerating, error, sessionActive,
  } = useAppStore();
  const [micOn, setMicOn] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const [typedQuestion, setTypedQuestion] = useState("");
  const wsRef = useInterviewSocket();

  useMicCapture(showOverlay && micOn, wsRef);

  const submitQuestion = () => {
    const q = typedQuestion.trim();
    if (!q || !wsRef.current) return;
    const st = useAppStore.getState();
    st.clearAnswer();
    st.setCurrentQuestion({
      text: q,
      category: "unknown",
      classification: {
        category: "unknown",
        technology: null,
        difficulty: null,
        requires_retrieval: false,
        requires_reasoning: false,
        requires_code_execution: false,
        requires_screen_context: false,
        confidence: 0,
      },
      confidence: 1,
    });
    st.setPipelineStatus({ stage: "detecting", message: "Processing your question…" });
    wsRef.current.send({ type: "question.text", payload: { text: q } });
    setTypedQuestion("");
  };

  useEffect(() => {
    if (session) return;
    apiClient
      .createSession()
      .then((s) => {
        setSession(s);
        useAppStore.getState().setError(null);
      })
      .catch((e) => useAppStore.getState().setError(e.message ?? "Backend not reachable"));
  }, [session, setSession]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey && e.shiftKey)) return;
      if (e.key === "H") { e.preventDefault(); toggleOverlay(); }
      if (e.key === "C") { e.preventDefault(); clearAnswer(); }
      if (e.key === "M") {
        e.preventDefault();
        const next = MODES[(MODES.indexOf(mode) + 1 + MODES.length) % MODES.length]!;
        setMode(next);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [mode, toggleOverlay, clearAnswer, setMode]);

  if (!showOverlay) {
    return (
      <div style={styles.invisibleBadge} onClick={toggleOverlay} title="Ctrl+Shift+H to reopen">
        🤖
      </div>
    );
  }

  return (
    <div style={styles.widget}>
      <div style={styles.header}>
        <div style={styles.titleRow}>
          <span style={styles.dot(sessionActive)} />
          <span style={styles.title}>Interview Copilot</span>
          <span style={styles.mode}>{mode}</span>
        </div>
        <div style={styles.headerBtns}>
          <button
            onClick={() => setMicOn((m) => !m)}
            style={{ ...styles.iconBtn, ...(micOn ? styles.micOn : {}) }}
            title={micOn ? "Mute microphone" : "Start listening"}
          >
            {micOn ? "🎙" : "🔇"}
          </button>
          <button
            onClick={() => setShowTranscript((s) => !s)}
            style={styles.iconBtn}
            title="Toggle live transcript"
          >
            📋
          </button>
          <button onClick={toggleOverlay} style={styles.minBtn} title="Hide (Ctrl+Shift+H)">
            −
          </button>
        </div>
      </div>

      <div style={styles.body}>
        <QuestionPanel />
        <AnswerPanel />
        {showTranscript && <LiveTranscript />}
      </div>

      <div style={styles.inputRow}>
        <input
          value={typedQuestion}
          onChange={(e) => setTypedQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") submitQuestion(); }}
          placeholder="Type a question and press Enter…"
          style={styles.input}
        />
        <button onClick={submitQuestion} style={styles.askBtn}>Ask</button>
      </div>

      <div style={styles.footer}>
        <span style={styles.stage}>
          {pipelineStatus
            ? `${STAGE_ICONS[pipelineStatus.stage] ?? "⚙️"} ${pipelineStatus.message}`
            : micOn
              ? "🎤 Listening…"
              : isGenerating
                ? "💬 Generating…"
                : "Idle — press 🎙 to start"}
        </span>
        <span style={styles.sessionInfo}>
          {session ? `#${session.id.slice(0, 6)}` : "connecting…"}
        </span>
      </div>
      {error && <div style={styles.error}>{error}</div>}
      <SettingsPanel />
    </div>
  );
};

const styles = {
  widget: {
    position: "fixed" as const,
    bottom: 16,
    right: 16,
    width: 440,
    maxWidth: "92vw",
    maxHeight: "80vh",
    display: "flex",
    flexDirection: "column" as const,
    background: "#0d1117",
    border: "1px solid #30363d",
    borderRadius: 12,
    boxShadow: "0 12px 40px rgba(0,0,0,0.55)",
    zIndex: 2147483000,
    overflow: "hidden",
    fontFamily: "'Segoe UI', system-ui, sans-serif",
    color: "#c9d1d9",
  },
  invisibleBadge: {
    position: "fixed" as const,
    bottom: 16,
    right: 16,
    width: 40,
    height: 40,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#161b22",
    border: "1px solid #30363d",
    borderRadius: "50%",
    cursor: "pointer",
    zIndex: 2147483000,
    boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px 14px",
    background: "#161b22",
    borderBottom: "1px solid #30363d",
    userSelect: "none" as const,
  },
  titleRow: { display: "flex", alignItems: "center", gap: 8 },
  dot: (active: boolean): React.CSSProperties => ({
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: active ? "#3fb950" : "#f85149",
  }),
  title: { fontSize: 13, fontWeight: 600, color: "#e6edf3" },
  mode: {
    background: "#21262d",
    padding: "2px 8px",
    borderRadius: 10,
    fontSize: 10,
    color: "#8b949e",
    textTransform: "capitalize" as const,
  },
  headerBtns: { display: "flex", alignItems: "center", gap: 6 },
  iconBtn: {
    background: "none",
    border: "none",
    fontSize: 14,
    cursor: "pointer",
    padding: "2px 6px",
    borderRadius: 6,
    color: "#8b949e",
  },
  micOn: { background: "#12261a", color: "#3fb950" },
  minBtn: {
    background: "none",
    border: "none",
    color: "#6e7681",
    cursor: "pointer",
    fontSize: 14,
    padding: "0 4px",
  },
  body: {
    display: "flex",
    flexDirection: "column" as const,
    overflow: "auto",
    minHeight: 0,
  },
  inputRow: {
    display: "flex",
    gap: 8,
    padding: "8px 12px",
    borderTop: "1px solid #21262d",
    background: "#161b22",
  },
  input: {
    flex: 1,
    background: "#0d1117",
    border: "1px solid #30363d",
    borderRadius: 6,
    color: "#c9d1d9",
    padding: "7px 10px",
    fontSize: 13,
    outline: "none",
  },
  askBtn: {
    background: "#238636",
    border: "1px solid #2ea043",
    color: "#fff",
    borderRadius: 6,
    padding: "6px 14px",
    fontSize: 12,
    fontWeight: 600,
    cursor: "pointer",
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 14px",
    borderTop: "1px solid #21262d",
    background: "#161b22",
    fontSize: 11,
    color: "#58a6ff",
  },
  stage: { flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const },
  sessionInfo: { color: "#484f58", fontSize: 10, fontFamily: "monospace" },
  error: {
    padding: "6px 14px",
    fontSize: 11,
    color: "#f85149",
    background: "#2d1513",
    borderTop: "1px solid #f85149",
  },
};

export default App;