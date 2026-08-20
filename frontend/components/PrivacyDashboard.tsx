"use client";

import { useEffect, useState } from "react";
import { getPreferences, updatePreferences, exportMyData, deleteAccount, Preferences, hasToken } from "../lib/api";

const TOGGLE_LABELS: Record<keyof Preferences, string> = {
  long_term_memory_enabled: "Remember context across conversations",
  voice_emotion_enabled: "Voice emotion analysis",
  wearable_integration_enabled: "Wearable device integration",
  research_participation_opt_in: "Contribute de-identified data to research",
  emergency_contacts_enabled: "Allow emergency-contact use (when configured)",
};

export default function PrivacyDashboard() {
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleted, setDeleted] = useState(false);

  async function load() {
    if (!hasToken()) {
      setError("Sign in to manage your privacy settings.");
      setLoading(false);
      return;
    }
    try {
      setPrefs(await getPreferences());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleToggle(key: keyof Preferences) {
    if (!prefs) return;
    const newValue = !prefs[key];
    setPrefs({ ...prefs, [key]: newValue }); // optimistic
    try {
      await updatePreferences({ [key]: newValue });
    } catch (e: any) {
      setError(e.message);
      load(); // revert on failure
    }
  }

  async function handleExport() {
    setExporting(true);
    try {
      const data = await exportMyData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sanjeevani-my-data.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setExporting(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      if (!deletePassword) { setError("Enter your password to confirm account deletion."); return; }
      await deleteAccount(deletePassword);
      setDeleted(true);
      localStorage.removeItem("mb_token");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setDeleting(false);
    }
  }

  if (deleted) {
    return (
      <div style={{ maxWidth: 560, margin: "80px auto", padding: "var(--space-3)", textAlign: "center" }}>
        <h1 style={{ fontSize: 22 }}>Your deletion request has been processed</h1>
        <p style={{ color: "var(--color-text-muted)" }}>
          Your account is deactivated and your encryption key has been revoked, so your
          content can no longer be read. Some records are retained longer for legal/audit
          purposes, as disclosed in the Privacy Policy.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 560, margin: "0 auto", padding: "var(--space-3)" }}>
      <h1 style={{ fontSize: 22 }}>Privacy Dashboard</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: -4 }}>
        Everything here is off unless you turn it on.
      </p>

      {error && (
        <div style={{ background: "var(--color-resource-bg)", border: "1px solid var(--color-resource)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          {error} {error.includes("Sign in") && <a href="/login" style={{ color: "var(--color-resource)" }}>Sign in</a>}
        </div>
      )}

      {loading && <p style={{ color: "var(--color-text-muted)" }}>Loading...</p>}

      {prefs && (
        <div style={{ background: "var(--color-surface)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-3)" }}>
          {(Object.keys(TOGGLE_LABELS) as (keyof Preferences)[]).map((key) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: "1px solid var(--color-primary-dim)" }}>
              <span style={{ fontSize: 15 }}>{TOGGLE_LABELS[key]}</span>
              <button
                onClick={() => handleToggle(key)}
                aria-pressed={prefs[key]}
                style={{
                  width: 44,
                  height: 24,
                  borderRadius: 12,
                  border: "none",
                  background: prefs[key] ? "var(--color-primary)" : "#D5D9D6",
                  position: "relative",
                  cursor: "pointer",
                }}
              >
                <span
                  style={{
                    position: "absolute",
                    top: 2,
                    left: prefs[key] ? 22 : 2,
                    width: 20,
                    height: 20,
                    borderRadius: "50%",
                    background: "white",
                    transition: "left 0.15s ease",
                  }}
                />
              </button>
            </div>
          ))}
        </div>
      )}

      <div style={{ background: "var(--color-surface)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-2)" }}>
        <h3 style={{ fontSize: 16, marginTop: 0 }}>Your data</h3>
        <p style={{ fontSize: 14, color: "var(--color-text-muted)" }}>
          Download the data Sanjeevani has stored for you — messages, mood entries, and journal entries — as a JSON file.
        </p>
        <button
          onClick={handleExport}
          disabled={exporting}
          style={{ background: "var(--color-primary)", color: "white", border: "none", borderRadius: "var(--radius)", padding: "10px 20px" }}
        >
          {exporting ? "Preparing export..." : "Export my data"}
        </button>
      </div>

      <div style={{ background: "var(--color-resource-bg)", border: "1px solid var(--color-resource)", borderRadius: "var(--radius)", padding: "var(--space-2)" }}>
        <h3 style={{ fontSize: 16, marginTop: 0, color: "var(--color-resource)" }}>Delete my account</h3>
        <p style={{ fontSize: 14 }}>
          This deactivates your account and permanently revokes your encryption key, so your
          content can no longer be decrypted by anyone. Some records (like safety assessments)
          may be retained longer for legal/audit compliance — see the Privacy Policy for details.
          This cannot be undone.
        </p>
        {!confirmingDelete ? (
          <button
            onClick={() => setConfirmingDelete(true)}
            style={{ background: "transparent", color: "var(--color-resource)", border: "1px solid var(--color-resource)", borderRadius: "var(--radius)", padding: "10px 20px" }}
          >
            Delete my account
          </button>
        ) : (
          <div>
            <p style={{ fontWeight: 600 }}>Are you sure? This is permanent.</p>
            <input type="password" value={deletePassword} onChange={(e) => setDeletePassword(e.target.value)} placeholder="Your password" aria-label="Account password" style={{ width: "100%", boxSizing: "border-box", padding: 10, marginBottom: 10, borderRadius: "var(--radius)", border: "1px solid var(--color-primary-dim)" }} />
            <button
              onClick={handleDelete}
              disabled={deleting}
              style={{ background: "var(--color-resource)", color: "white", border: "none", borderRadius: "var(--radius)", padding: "10px 20px", marginRight: 8 }}
            >
              {deleting ? "Processing..." : "Yes, delete permanently"}
            </button>
            <button
              onClick={() => setConfirmingDelete(false)}
              style={{ background: "transparent", border: "1px solid var(--color-text-muted)", borderRadius: "var(--radius)", padding: "10px 20px" }}
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
