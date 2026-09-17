import React, { useRef, useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";

export const LiveTranscript: React.FC = () => {
  const { transcript, pipelineStatus } = useAppStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>Live Transcript</span>
        <span style={styles.stage}>
          {pipelineStatus?.stage === "transcribing" ? "🔴 Listening…" : "⚪"}
        </span>
      </div>
      <div style={styles.scroll}>
        {transcript.length === 0 && (
          <div style={styles.empty}>Waiting for audio…</div>
        )}
        {transcript.map((t, i) => (
          <div key={i} style={styles.line(t.speaker)}>
            {t.speaker && <span style={styles.speaker}>{t.speaker}: </span>}
            <span style={styles.text}>{t.text}</span>
            <span style={styles.confidence}>
              {t.confidence ? `${Math.round(t.confidence * 100)}%` : ""}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

const styles = {
  container: { flex: 1, display: "flex", flexDirection: "column" as const, minHeight: 140 },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "6px 12px",
    borderBottom: "1px solid #21262d",
    fontSize: 12,
    color: "#8b949e",
  },
  title: { fontWeight: 600, letterSpacing: 0.5, textTransform: "uppercase" as const },
  stage: { fontSize: 11 },
  scroll: { flex: 1, overflow: "auto", padding: "8px 12px", maxHeight: 200 },
  empty: { color: "#484f58", fontSize: 12, fontStyle: "italic" },
  line: (speaker?: string): React.CSSProperties => ({
    padding: "3px 0",
    borderBottom: "1px solid #161b22",
    color: speaker === "interviewer" ? "#79c0ff" : "#c9d1d9",
    fontSize: 13,
  }),
  speaker: { fontWeight: 600, marginRight: 6 },
  text: {},
  confidence: { color: "#484f58", fontSize: 10, marginLeft: 8 },
};
