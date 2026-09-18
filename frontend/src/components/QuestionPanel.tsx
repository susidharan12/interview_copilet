import React from "react";
import { useAppStore } from "@/store/useAppStore";

const CATEGORY_LABELS: Record<string, string> = {
  technical: "🔧 Technical",
  coding: "💻 Coding",
  debugging: "🐛 Debugging",
  system_design: "🏗️ System Design",
  architecture: "🏛️ Architecture",
  scenario: "🎭 Scenario",
  behavioral: "💬 Behavioral",
  project: "📁 Project",
  resume: "📄 Resume",
  sql: "🗃️ SQL",
  follow_up: "↩️ Follow-up",
  clarification: "❓ Clarification",
  unknown: "❓ Unknown",
};

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: "#3fb950",
  medium: "#d29922",
  hard: "#f85149",
};

export const QuestionPanel: React.FC = () => {
  const { currentQuestion, isGenerating } = useAppStore();

  if (!currentQuestion) {
    return (
      <div style={styles.container}>
        <div style={styles.empty}>Waiting for a question…</div>
      </div>
    );
  }

  const classification = currentQuestion.classification ?? {
    category: "unknown",
    difficulty: null,
    technology: null,
  };

  return (
    <div style={styles.container}>
      <div style={styles.badges}>
        <span style={styles.categoryBadge}>
          {CATEGORY_LABELS[currentQuestion.category] ?? currentQuestion.category}
        </span>
        {classification.difficulty && (
          <span
            style={{
              ...styles.diffBadge,
              color: DIFFICULTY_COLORS[classification.difficulty] ?? "#8b949e",
            }}
          >
            {classification.difficulty}
          </span>
        )}
        {classification.technology && (
          <span style={styles.techBadge}>{classification.technology}</span>
        )}
        {isGenerating && <span style={styles.generating}>Generating…</span>}
      </div>
      <div style={styles.question}>{currentQuestion.text}</div>
    </div>
  );
};

const styles = {
  container: {
    padding: "12px 16px",
    borderBottom: "1px solid #21262d",
    background: "#0d1117",
  },
  empty: { color: "#484f58", fontSize: 13, padding: "8px 0" },
  badges: { display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" as const },
  categoryBadge: {
    background: "#21262d",
    color: "#c9d1d9",
    padding: "2px 10px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 600,
  },
  diffBadge: { fontSize: 12, fontWeight: 600, padding: "2px 6px" },
  techBadge: {
    background: "#1f2937",
    color: "#a5d6ff",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
  },
  generating: { color: "#58a6ff", fontSize: 11, padding: "2px 0" },
  question: { fontSize: 15, fontWeight: 500, color: "#e6edf3", lineHeight: 1.5 },
};
