"use client";

import { useState } from "react";
import { sendMessage, ChatResponse } from "../lib/api";
import CrisisBanner from "./CrisisBanner";

interface Turn {
  sender: "user" | "ai";
  text: string;
}

export default function ChatWindow() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [input, setInput] = useState("");
  const [chatId, setChatId] = useState<string | undefined>(undefined);
  const [lastSafety, setLastSafety] = useState<ChatResponse["safety"] | null>(null);
  const [resourcesText, setResourcesText] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  async function handleSend() {
    if (!input.trim() || sending) return;
    const userText = input;
    setInput("");
    setTurns((t) => [...t, { sender: "user", text: userText }]);
    setSending(true);
    try {
      const res = await sendMessage(userText, chatId);
      setChatId(res.chat_id);
      setLastSafety(res.safety);
      setResourcesText(res.resources_text);
      setTurns((t) => [...t, { sender: "ai", text: res.ai_response }]);
    } catch (e) {
      setTurns((t) => [...t, { sender: "ai", text: "Something went wrong sending that. Please try again." }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ maxWidth: 640, margin: "0 auto", padding: "var(--space-3)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ fontWeight: 600, fontSize: 22, margin: 0 }}>Sanjeevani</h1>
        <a href="/login" style={{ fontSize: 13 }}>Account</a>
      </div>
      <p style={{ color: "var(--color-text-muted)", marginTop: -4 }}>
        A space to reflect. Not a substitute for therapy or medical care.
      </p>

      {resourcesText && <CrisisBanner text={resourcesText} />}

      <div
        style={{
          background: "var(--color-surface)",
          borderRadius: "var(--radius)",
          padding: "var(--space-2)",
          minHeight: 320,
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-1)",
        }}
      >
        {turns.length === 0 && (
          <p style={{ color: "var(--color-text-muted)" }}>
            Start whenever you're ready. There's no wrong way to begin.
          </p>
        )}
        {turns.map((t, i) => (
          <div
            key={i}
            style={{
              alignSelf: t.sender === "user" ? "flex-end" : "flex-start",
              background: t.sender === "user" ? "var(--color-primary-dim)" : "var(--color-bg)",
              borderRadius: "var(--radius)",
              padding: "10px 14px",
              maxWidth: "80%",
            }}
          >
            {t.text}
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "var(--space-1)", marginTop: "var(--space-2)" }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type how you're feeling..."
          aria-label="Message"
          style={{
            flex: 1,
            padding: "12px 14px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-primary-dim)",
            fontSize: 16,
          }}
        />
        <button
          onClick={handleSend}
          disabled={sending}
          style={{
            background: "var(--color-primary)",
            color: "white",
            border: "none",
            borderRadius: "var(--radius)",
            padding: "0 20px",
          }}
        >
          Send
        </button>
      </div>

      {lastSafety && lastSafety.concern_level !== "low" && (
        <p style={{ fontSize: 13, color: "var(--color-text-muted)", marginTop: 8 }}>
          This conversation has been flagged for a caring check-in by our review team — that's
          automatic and confidential, not something you need to do anything about.
        </p>
      )}

      <a
        href="/crisis-resources"
        style={{
          display: "inline-block",
          marginTop: "var(--space-3)",
          fontSize: 13,
          color: "var(--color-resource)",
        }}
      >
        Crisis resources — always available
      </a>
      <div style={{ display: "flex", gap: 14, marginTop: 10, flexWrap: "wrap" }}>
        <a href="/mood" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Mood</a>
        <a href="/journal" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Journal</a>
        <a href="/history" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>History</a>
        <a href="/contacts" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Emergency contacts</a>
        <a href="/summary" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Summary</a>
        <a href="/privacy" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Privacy</a>
        <a href="/login" style={{ fontSize: 13, color: "var(--color-text-muted)" }}>Reviewer / staff sign in</a>
      </div>
    </div>
  );
}
