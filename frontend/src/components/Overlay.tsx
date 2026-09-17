import React, { useEffect } from "react";
import { useAppStore } from "@/store/useAppStore";

export const Overlay: React.FC = () => {
  const {
    showOverlay, toggleOverlay,
    pipelineStatus, currentQuestion, answerText, isGenerating, mode,
    clearAnswer,
  } = useAppStore();

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey) {
        if (e.key === "H") { e.preventDefault(); toggleOverlay(); }
        if (e.key === "C") { e.preventDefault(); clearAnswer(); }
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  if (!showOverlay) return null;

  return (
    <div style={styles.overlay}>
      <div style={styles.dragBar}>
        <span style={styles.title}>Interview Copilot · {mode}</span>
        <button onClick={toggleOverlay} style={styles.hideBtn}>Hide</button>
      </div>
      {currentQuestion && (
        <div style={styles.question}>{currentQuestion.text}</div>
      )}
      {isGenerating && (
        <div style={styles.stage}>{pipelineStatus?.message ?? "Thinking…"}</div>
      )}
      <div style={styles.answer}>
        {answerText || <span style={styles.placeholder}>Waiting for answer…</span>}
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: "fixed" as const,
    bottom: 12,
    right: 12,
    width: 380,
    maxHeight: 300,
    background: "rgba(13,17,23,0.95)",
    border: "1px solid #30363d",
    borderRadius: 10,
    padding: 10,
    zIndex: 10000,
    display: "flex",
    flexDirection: "column" as const,
    boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
  },
  dragBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  title: { fontSize: 11, fontWeight: 600, color: "#8b949e" },
  hideBtn: {
    background: "none",
    border: "none",
    color: "#6e7681",
    cursor: "pointer",
    fontSize: 11,
  },
  question: {
    fontSize: 13,
    fontWeight: 600,
    color: "#79c0ff",
    marginBottom: 6,
    lineHeight: 1.4,
  },
  stage: { fontSize: 11, color: "#58a6ff", marginBottom: 4 },
  answer: {
    fontSize: 12,
    color: "#c9d1d9",
    lineHeight: 1.5,
    overflow: "auto",
    maxHeight: 180,
    flex: 1,
  },
  placeholder: { color: "#484f58", fontStyle: "italic" },
};
