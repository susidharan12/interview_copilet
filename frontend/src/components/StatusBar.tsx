import React from "react";
import { useAppStore } from "@/store/useAppStore";

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

export const StatusBar: React.FC = () => {
  const { pipelineStatus, sessionActive, mode, error } = useAppStore();

  return (
    <div style={styles.bar}>
      <div style={styles.left}>
        <span style={styles.dot(sessionActive)} />
        <span style={styles.label}>
          {sessionActive ? "Session Active" : "No Session"}
        </span>
        <span style={styles.mode}>{mode}</span>
      </div>
      <div style={styles.center}>
        {pipelineStatus && (
          <span style={styles.stage}>
            {STAGE_ICONS[pipelineStatus.stage] ?? "⚙️"}{" "}
            {pipelineStatus.message}
          </span>
        )}
      </div>
      <div style={styles.right}>
        {error && <span style={styles.error}>⚠ {error}</span>}
        <span style={styles.version}>v0.1.0</span>
      </div>
    </div>
  );
};

const styles = {
  bar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 16px",
    background: "#161b22",
    borderBottom: "1px solid #30363d",
    fontSize: 13,
    gap: 12,
  },
  left: { display: "flex", alignItems: "center", gap: 10 },
  center: { display: "flex", alignItems: "center", gap: 8, flex: 1, justifyContent: "center" as const },
  right: { display: "flex", alignItems: "center", gap: 10 },
  dot: (active: boolean): React.CSSProperties => ({
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: active ? "#3fb950" : "#f85149",
    display: "inline-block",
  }),
  label: { color: "#c9d1d9", fontWeight: 500 },
  mode: {
    background: "#21262d",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    color: "#8b949e",
  },
  stage: { color: "#58a6ff", fontSize: 12 },
  error: { color: "#f85149", fontSize: 12 },
  version: { color: "#484f58", fontSize: 11 },
};
