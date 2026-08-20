"use client";

import { useEffect, useState } from "react";
import { logMood, listMoods, MoodEntry, hasToken } from "../lib/api";

const TAG_OPTIONS = ["anxious", "tired", "grateful", "stressed", "calm", "hopeful", "lonely", "proud"];

export default function MoodPage() {
  const [score, setScore] = useState(5);
  const [tags, setTags] = useState<string[]>([]);
  const [note, setNote] = useState("");
  const [entries, setEntries] = useState<MoodEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!hasToken()) {
      setError("Sign in to track your mood.");
      setLoading(false);
      return;
    }
    try {
      setEntries(await listMoods());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function toggleTag(tag: string) {
    setTags((t) => (t.includes(tag) ? t.filter((x) => x !== tag) : [...t, tag]));
  }

  async function handleSave() {
    setSaving(true);
    try {
      await logMood(score, tags, note || undefined);
      setTags([]);
      setNote("");
      await load();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  const maxScore = 10;
  const chartEntries = [...entries].reverse().slice(-30); // oldest → newest, last 30

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "var(--space-3)" }}>
      <h1 style={{ fontSize: 22 }}>Mood</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: -4 }}>
        A quick check-in — however you're doing is okay to log.
      </p>

      {error && (
        <div style={{ background: "var(--color-resource-bg)", border: "1px solid var(--color-resource)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          {error} {error.includes("Sign in") && <a href="/login" style={{ color: "var(--color-resource)" }}>Sign in</a>}
        </div>
      )}

      <div style={{ background: "var(--color-surface)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-3)" }}>
        <label style={{ fontSize: 14, color: "var(--color-text-muted)" }}>
          How are you feeling? ({score}/10)
        </label>
        <input
          type="range"
          min={1}
          max={10}
          value={score}
          onChange={(e) => setScore(Number(e.target.value))}
          style={{ width: "100%", margin: "8px 0" }}
        />

        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, margin: "8px 0" }}>
          {TAG_OPTIONS.map((tag) => (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              style={{
                padding: "4px 12px",
                borderRadius: 999,
                border: "1px solid var(--color-primary-dim)",
                background: tags.includes(tag) ? "var(--color-primary)" : "transparent",
                color: tags.includes(tag) ? "white" : "var(--color-text)",
                fontSize: 13,
              }}
            >
              {tag}
            </button>
          ))}
        </div>

        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Anything you want to add? (optional)"
          rows={2}
          style={{
            width: "100%",
            padding: 10,
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-primary-dim)",
            fontSize: 15,
            fontFamily: "inherit",
            resize: "vertical",
          }}
        />

        <button
          onClick={handleSave}
          disabled={saving}
          style={{
            marginTop: 8,
            background: "var(--color-primary)",
            color: "white",
            border: "none",
            borderRadius: "var(--radius)",
            padding: "10px 20px",
          }}
        >
          {saving ? "Logging..." : "Log mood"}
        </button>
      </div>

      {!loading && chartEntries.length > 0 && (
        <div style={{ background: "var(--color-surface)", borderRadius: "var(--radius)", padding: "var(--space-2)", marginBottom: "var(--space-2)" }}>
          <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: 0 }}>Last {chartEntries.length} entries</p>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 100 }}>
            {chartEntries.map((e) => (
              <div
                key={e.id}
                title={`${e.mood_score}/10 — ${new Date(e.logged_at).toLocaleDateString()}`}
                style={{
                  flex: 1,
                  height: `${(e.mood_score / maxScore) * 100}%`,
                  background: "var(--color-primary)",
                  borderRadius: 2,
                  minHeight: 4,
                }}
              />
            ))}
          </div>
        </div>
      )}

      {loading && <p style={{ color: "var(--color-text-muted)" }}>Loading...</p>}
    </div>
  );
}
