import React from "react";
import { useAppStore } from "@/store/useAppStore";

export const SourcesPanel: React.FC = () => {
  const { sources } = useAppStore();
  if (sources.length === 0) return null;

  return (
    <div style={styles.container}>
      <div style={styles.header}>Retrieved Sources</div>
      {sources.map((s, i) => (
        <div key={i} style={styles.card}>
          <div style={styles.meta}>
            <span>Doc {s.document_id.slice(0, 8)}</span>
            <span style={styles.score}>score: {s.score.toFixed(3)}</span>
          </div>
          <div style={styles.preview}>{s.content_preview}</div>
        </div>
      ))}
    </div>
  );
};

const styles = {
  container: { padding: "6px 12px", borderTop: "1px solid #161b22", background: "#0d1117" },
  header: { fontSize: 11, fontWeight: 600, color: "#8b949e", marginBottom: 6 },
  card: {
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 6,
    padding: "8px 10px",
    marginBottom: 6,
    fontSize: 12,
    color: "#8b949e",
  },
  meta: { display: "flex", justifyContent: "space-between", marginBottom: 4 },
  score: { color: "#58a6ff", fontSize: 10 },
  preview: { lineHeight: 1.4 },
};
