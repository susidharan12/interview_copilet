import React, { useEffect, useState } from "react";
import { apiClient } from "@/api/client";
import type { Profile } from "@/types";

export const ProfilePanel: React.FC = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient
      .getProfile()
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={styles.empty}>Loading profile…</div>;
  if (!profile) return <div style={styles.empty}>No profile loaded</div>;

  return (
    <div style={styles.container}>
      <div style={styles.row}>
        <span style={styles.label}>Name:</span>
        <span style={styles.value}>{profile.name}</span>
      </div>
      <div style={styles.row}>
        <span style={styles.label}>Experience:</span>
        <span style={styles.value}>{profile.experience_years ?? "N/A"} years</span>
      </div>
      <div style={styles.row}>
        <span style={styles.label}>Target role:</span>
        <span style={styles.value}>{profile.target_role ?? "Not set"}</span>
      </div>
      {profile.skills.length > 0 && (
        <div style={styles.row}>
          <span style={styles.label}>Skills:</span>
          <div style={styles.tags}>
            {profile.skills.map((s) => (
              <span key={s} style={styles.tag}>{s}</span>
            ))}
          </div>
        </div>
      )}
      {profile.resume_summary && (
        <div style={styles.summary}>{profile.resume_summary}</div>
      )}
    </div>
  );
};

const styles = {
  container: { padding: "12px 16px" },
  row: { display: "flex", gap: 8, marginBottom: 8, fontSize: 13 },
  label: { color: "#8b949e", fontWeight: 600, minWidth: 90 },
  value: { color: "#c9d1d9" },
  tags: { display: "flex", flexWrap: "wrap" as const, gap: 4 },
  tag: {
    background: "#21262d",
    padding: "2px 8px",
    borderRadius: 4,
    fontSize: 11,
    color: "#a5d6ff",
  },
  summary: { marginTop: 10, fontSize: 12, color: "#8b949e", lineHeight: 1.5 },
  empty: { padding: "12px 16px", fontSize: 12, color: "#484f58" },
};
