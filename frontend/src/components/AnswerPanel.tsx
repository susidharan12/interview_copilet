import React, { useRef, useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";

export const AnswerPanel: React.FC = () => {
  const { answerText, answerDone, isGenerating, sources } = useAppStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [answerText]);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>Answer</span>
        {answerDone && (
          <span style={styles.meta}>
            {answerDone.latency_ms}ms · {answerDone.mode}
          </span>
        )}
      </div>
      <div style={styles.scroll} ref={scrollRef}>
        {answerText ? (
          <div style={styles.text}>
            {answerText.split("\n").map((line, i) => (
              <p key={i} style={{ marginBottom: line ? 8 : 4 }}>
                {line || "\u00A0"}
              </p>
            ))}
            {isGenerating && <span style={styles.cursor}>▌</span>}
          </div>
        ) : (
          <div style={styles.empty}>Answer will appear here…</div>
        )}
      </div>
      {sources.length > 0 && (
        <div style={styles.sources}>
          <span style={styles.sourcesLabel}>Sources:</span>
          {sources.map((s, i) => (
            <span key={i} style={styles.sourceItem}>
              {s.content_preview?.slice(0, 80)}…
            </span>
          ))}
        </div>
      )}
      {answerDone?.validation && (
        <div style={styles.validation}>
          {answerDone.validation.passed ? "✅ Verified" : "⚠ Unverified"} ·{" "}
          Confidence: {Math.round((answerDone.validation.confidence ?? 0) * 100)}%
        </div>
      )}
    </div>
  );
};

const styles = {
  container: { display: "flex", flexDirection: "column" as const, flex: 1 },
  header: {
    display: "flex",
    justifyContent: "space-between",
    padding: "6px 12px",
    borderBottom: "1px solid #21262d",
    fontSize: 12,
    color: "#8b949e",
  },
  title: { fontWeight: 600, letterSpacing: 0.5, textTransform: "uppercase" as const },
  meta: { fontSize: 11, color: "#484f58" },
  scroll: { flex: 1, overflow: "auto", padding: "12px 16px", minHeight: 200 },
  text: { fontSize: 14, lineHeight: 1.7, color: "#e6edf3" },
  empty: { color: "#484f58", fontSize: 13, fontStyle: "italic" },
  cursor: { color: "#58a6ff", animation: "blink 1s step-end infinite" },
  sources: { padding: "8px 12px", borderTop: "1px solid #21262d", fontSize: 11, color: "#8b949e" },
  sourcesLabel: { fontWeight: 600, marginRight: 6 },
  sourceItem: { display: "inline-block", marginRight: 8, color: "#6e7681" },
  validation: { padding: "4px 12px", fontSize: 11, color: "#7ee787" },
};
