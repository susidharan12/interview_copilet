import React from "react";
import { useAppStore } from "@/store/useAppStore";

export const ConversationHistory: React.FC = () => {
  const { history } = useAppStore();

  return (
    <div style={styles.container}>
      <div style={styles.header}>Conversation History ({history.length})</div>
      <div style={styles.scroll}>
        {history.map((h, i) => (
          <div key={i} style={styles.item}>
            <div style={styles.q}>{h.question.slice(0, 100)}</div>
            <div style={styles.a}>{h.answer.slice(0, 120)}…</div>
            <div style={styles.meta}>
              {h.category} · {new Date(h.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
        {history.length === 0 && <div style={styles.empty}>No history yet</div>}
      </div>
    </div>
  );
};

const styles = {
  container: { display: "flex", flexDirection: "column" as const },
  header: {
    padding: "6px 12px",
    borderBottom: "1px solid #21262d",
    fontSize: 12,
    fontWeight: 600,
    color: "#8b949e",
  },
  scroll: { overflow: "auto", maxHeight: 260, padding: "8px 12px" },
  item: {
    padding: "8px 10px",
    borderBottom: "1px solid #161b22",
    borderRadius: 4,
    marginBottom: 6,
    background: "#0d1117",
  },
  q: { fontSize: 13, fontWeight: 600, color: "#79c0ff", marginBottom: 4 },
  a: { fontSize: 12, color: "#8b949e", lineHeight: 1.4 },
  meta: { fontSize: 10, color: "#484f58", marginTop: 4 },
  empty: { fontSize: 12, color: "#484f58", fontStyle: "italic" },
};
