import React, { useState } from "react";
import { useAppStore } from "@/store/useAppStore";
import type { AnswerMode } from "@/types";
import { apiClient } from "@/api/client";

const MODES: { value: AnswerMode; label: string; description: string }[] = [
  { value: "quick", label: "Quick", description: "1-2 sentence direct answer" },
  { value: "interview", label: "Interview", description: "Direct + explanation + example" },
  { value: "senior", label: "Senior", description: "Architecture + trade-offs + production" },
  { value: "coding", label: "Coding", description: "Approach + code + complexity + edges" },
  { value: "scenario", label: "Scenario", description: "Situation + investigation + solution" },
];

export const SettingsPanel: React.FC = () => {
  const { mode, setMode, toggleSettings, settingsPanelOpen } = useAppStore();
  const [docFile, setDocFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState("technical");
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  if (!settingsPanelOpen) return null;

  const handleUpload = async () => {
    if (!docFile) return;
    setUploading(true);
    try {
      const res = await apiClient.uploadDocument(docFile, docType, []);
      setUploadMessage(`Uploaded: ${res.id.slice(0, 8)}… (${res.status})`);
      setDocFile(null);
    } catch (e) {
      setUploadMessage(`Upload failed: ${e}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.panel}>
        <div style={styles.header}>
          <span>Settings</span>
          <button onClick={toggleSettings} style={styles.closeBtn}>✕</button>
        </div>

        <div style={styles.section}>
          <div style={styles.label}>Answer Mode</div>
          {MODES.map((m) => (
            <button
              key={m.value}
              onClick={() => setMode(m.value)}
              style={{ ...styles.modeBtn, ...(mode === m.value ? styles.modeBtnActive : {}) }}
            >
              <strong>{m.label}</strong>
              <span style={styles.modeDesc}>{m.description}</span>
            </button>
          ))}
        </div>

        <div style={styles.section}>
          <div style={styles.label}>Upload Document</div>
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            style={styles.select}
          >
            <option value="resume">Resume</option>
            <option value="project">Project Docs</option>
            <option value="notes">Interview Notes</option>
            <option value="technical">Technical Doc</option>
            <option value="job_description">Job Description</option>
          </select>
          <input
            type="file"
            onChange={(e) => setDocFile(e.target.files?.[0] ?? null)}
            style={styles.fileInput}
            accept=".pdf,.md,.txt,.json"
          />
          <button
            onClick={handleUpload}
            disabled={!docFile || uploading}
            style={styles.uploadBtn}
          >
            {uploading ? "Uploading…" : "Upload & Ingest"}
          </button>
          {uploadMessage && <div style={styles.uploadMsg}>{uploadMessage}</div>}
        </div>

        <div style={styles.section}>
          <div style={styles.label}>Keyboard Shortcuts</div>
          <div style={styles.shortcut}>Ctrl+Shift+H: Hide/Show Overlay</div>
          <div style={styles.shortcut}>Ctrl+Shift+M: Switch Mode</div>
          <div style={styles.shortcut}>Ctrl+Shift+C: Clear Answer</div>
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: "fixed" as const,
    inset: 0,
    background: "rgba(0,0,0,0.5)",
    display: "flex",
    justifyContent: "flex-end",
    zIndex: 1000,
  },
  panel: {
    width: 340,
    background: "#161b22",
    borderLeft: "1px solid #30363d",
    padding: 20,
    overflowY: "auto" as const,
    height: "100%",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: 16,
    fontWeight: 600,
    color: "#e6edf3",
    marginBottom: 18,
  },
  closeBtn: {
    background: "none",
    border: "none",
    color: "#8b949e",
    cursor: "pointer",
    fontSize: 18,
    padding: "0 4px",
  },
  section: { marginBottom: 22 },
  label: { fontSize: 12, fontWeight: 600, color: "#8b949e", marginBottom: 8, textTransform: "uppercase" as const },
  modeBtn: {
    display: "block",
    width: "100%",
    textAlign: "left" as const,
    background: "#0d1117",
    border: "1px solid #21262d",
    color: "#c9d1d9",
    padding: "8px 12px",
    borderRadius: 6,
    marginBottom: 6,
    cursor: "pointer",
    fontSize: 13,
  },
  modeBtnActive: { borderColor: "#58a6ff", background: "#0d2244" },
  modeDesc: { display: "block", fontSize: 11, color: "#6e7681", marginTop: 2 },
  select: {
    background: "#0d1117",
    border: "1px solid #21262d",
    color: "#c9d1d9",
    padding: "6px 10px",
    borderRadius: 4,
    fontSize: 12,
    width: "100%",
    marginBottom: 8,
  },
  fileInput: { fontSize: 11, color: "#8b949e", marginBottom: 8 },
  uploadBtn: {
    width: "100%",
    background: "#238636",
    border: "1px solid #2ea043",
    color: "#fff",
    padding: "7px 12px",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 12,
    fontWeight: 600,
  },
  uploadMsg: { fontSize: 11, color: "#8b949e", marginTop: 6 },
  shortcut: { fontSize: 12, color: "#6e7681", padding: "3px 0", fontFamily: "monospace" },
};
