"use client";

import { useEffect, useState } from "react";
import { createJournal, listJournals, JournalEntry, hasToken } from "../lib/api";

const PROMPTS = [
  "What's one thing that's been on your mind today?",
  "What's something you're grateful for right now?",
  "What's a small win from today, no matter how minor?",
  "What's weighing on you that you haven't said out loud?",
];

export default function JournalPage() {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [content, setContent] = useState("");
  const [prompt, setPrompt] = useState(PROMPTS[0]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!hasToken()) {
      setError("Sign in to see your journal.");
      setLoading(false);
      return;
    }
    try {
      const data = await listJournals();
      setEntries(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSave() {
    if (!content.trim()) return;
    setSaving(true);
    try {
      await createJournal(content, prompt);
      setContent("");
      setPrompt(PROMPTS[Math.floor(Math.random() * PROMPTS.length)]);
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "var(--space-3)" }}>
      <h1 style={{ fontSize: 22 }}>Journal</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: -4 }}>
        Private, encrypted, just for you.
      </p>

      {error && (
        <div style={{ background: "var(--color-resource-bg)", border: "1px solid var(--color-resource)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          {error} {error.includes("Sign in") && <a href="/login" style={{ color: "var(--color-resource)" }}>Sign in</a>}
        </div>
      )}

      <div style={{ background: "var(--color-surface)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-3)" }}>
        <p style={{ fontStyle: "italic", color: "var(--color-text-muted)", marginTop: 0 }}>{prompt}</p>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Write whatever comes to mind..."
          rows={5}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-primary-dim)",
            fontSize: 16,
            fontFamily: "inherit",
            resize: "vertical",
          }}
        />
        <button
          onClick={handleSave}
          disabled={saving || !content.trim()}
          style={{
            marginTop: 8,
            background: "var(--color-primary)",
            color: "white",
            border: "none",
            borderRadius: "var(--radius)",
            padding: "10px 20px",
          }}
        >
          {saving ? "Saving..." : "Save entry"}
        </button>
      </div>

      {loading ? (
        <p style={{ color: "var(--color-text-muted)" }}>Loading...</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
          {entries.map((e) => (
            <div key={e.id} style={{ background: "var(--color-surface)", borderRadius: "var(--radius)", padding: "var(--space-2)" }}>
              <p style={{ fontSize: 12, color: "var(--color-text-muted)", margin: 0 }}>
                {new Date(e.created_at).toLocaleDateString()}
              </p>
              {e.prompt_used && <p style={{ fontSize: 13, fontStyle: "italic", color: "var(--color-text-muted)", margin: "4px 0" }}>{e.prompt_used}</p>}
              <p style={{ margin: 0 }}>{e.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
