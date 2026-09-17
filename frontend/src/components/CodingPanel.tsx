import React from "react";
import { useAppStore } from "@/store/useAppStore";

export const CodingPanel: React.FC = () => {
  const { currentCode } = useAppStore();
  if (!currentCode) return null;

  return (
    <div style={styles.container}>
      <div style={styles.header}>Code</div>
      <pre style={styles.code}>{currentCode}</pre>
    </div>
  );
};

const styles = {
  container: {
    padding: "8px 12px",
    borderTop: "1px solid #21262d",
    background: "#0d1117",
  },
  header: { fontSize: 11, fontWeight: 600, color: "#8b949e", marginBottom: 6 },
  code: {
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 6,
    padding: "10px 12px",
    fontSize: 12,
    lineHeight: 1.5,
    color: "#e6edf3",
    overflow: "auto",
    maxHeight: 300,
    fontFamily: "'Fira Code', 'Consolas', monospace",
    whiteSpace: "pre-wrap" as const,
    margin: 0,
  },
};
