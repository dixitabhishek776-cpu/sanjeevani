"use client";

import { useEffect, useState } from "react";
import { getAlerts, acknowledgeAlert, resolveAlert, Alert, hasToken } from "../lib/api";

const LEVEL_COLORS: Record<string, string> = {
  low: "var(--color-primary)",
  moderate: "#B98A3E",
  high: "var(--color-resource)",
  immediate: "#A83232",
};

export default function ReviewerDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("pending_review");
  const [acting, setActing] = useState<string | null>(null);
  const [notes, setNotes] = useState<Record<string,string>>({});

  async function load() {
    if (!hasToken()) {
      setError("You need to sign in with a reviewer account first.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getAlerts(statusFilter);
      setAlerts(data);
    } catch (e: any) {
      setError(e.message || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // Poll every 20s so urgent alerts surface without a manual refresh.
    const interval = setInterval(load, 20000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  async function handleAcknowledge(id: string) {
    setActing(id);
    try {
      await acknowledgeAlert(id);
      await load();
    } catch (e) {
      // no-op — load() will surface any persistent error state
    } finally {
      setActing(null);
    }
  }

  async function handleResolve(id: string) { setActing(id); try { await resolveAlert(id, notes[id] || ""); await load(); } finally { setActing(null); } }

  const sorted = [...alerts].sort((a, b) => {
    const rank: Record<string, number> = { immediate: 3, high: 2, moderate: 1, low: 0 };
    return rank[b.concern_level] - rank[a.concern_level];
  });

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: "var(--space-3)" }}>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Safety Alert Queue</h1>
      <p style={{ color: "var(--color-text-muted)", marginTop: 0, fontSize: 14 }}>
        Reviewer-only. Every acknowledgment is audit-logged. Immediate-level alerts require action, not just acknowledgment — escalate per protocol.
      </p>

      <div style={{ display: "flex", gap: 8, margin: "var(--space-2) 0" }}>
        {["pending_review", "acknowledged", "resolved"].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            style={{
              padding: "6px 14px",
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-primary-dim)",
              background: statusFilter === s ? "var(--color-primary)" : "transparent",
              color: statusFilter === s ? "white" : "var(--color-text)",
              fontSize: 14,
            }}
          >
            {s === "pending_review" ? "Pending" : s === "acknowledged" ? "Acknowledged" : "Resolved"}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ background: "var(--color-resource-bg)", border: "1px solid var(--color-resource)", borderRadius: "var(--radius)", padding: "var(--space-2)" }}>
          {error}{" "}
          {error.includes("sign in") && (
            <a href="/login" style={{ color: "var(--color-resource)", fontWeight: 600 }}>
              Go to sign in
            </a>
          )}
        </div>
      )}

      {loading && !error && <p style={{ color: "var(--color-text-muted)" }}>Loading...</p>}

      {!loading && !error && sorted.length === 0 && (
        <p style={{ color: "var(--color-text-muted)" }}>No alerts in this queue right now.</p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-1)" }}>
        {sorted.map((alert) => (
          <div
            key={alert.id}
            style={{
              background: "var(--color-surface)",
              borderRadius: "var(--radius)",
              padding: "var(--space-2)",
              borderLeft: `4px solid ${LEVEL_COLORS[alert.concern_level] || "var(--color-primary)"}`,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span
                style={{
                  fontWeight: 700,
                  textTransform: "uppercase",
                  fontSize: 12,
                  letterSpacing: 0.5,
                  color: LEVEL_COLORS[alert.concern_level] || "var(--color-primary)",
                }}
              >
                {alert.concern_level}
              </span>
              <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
                {new Date(alert.created_at).toLocaleString()}
              </span>
            </div>
            <p style={{ margin: "8px 0" }}>{alert.explanation}</p>
            {statusFilter !== "resolved" && <textarea value={notes[alert.id] || ""} onChange={(e) => setNotes({...notes,[alert.id]:e.target.value})} placeholder="Reviewer resolution notes (optional)" style={{width:"100%",margin:"8px 0",minHeight:60}} />}
            {statusFilter === "pending_review" && (
              <button
                onClick={() => handleAcknowledge(alert.id)}
                disabled={acting === alert.id}
                style={{
                  background: "var(--color-primary)",
                  color: "white",
                  border: "none",
                  borderRadius: "var(--radius)",
                  padding: "8px 16px",
                  fontSize: 14,
                }}
              >
                {acting === alert.id ? "Acknowledging..." : "Acknowledge"}
              </button>
            )}
            {statusFilter === "acknowledged" && <button onClick={() => handleResolve(alert.id)} disabled={acting === alert.id} style={{marginLeft:8,padding:"8px 16px"}}>{acting === alert.id ? "Resolving..." : "Resolve"}</button>}
          </div>
        ))}
      </div>
    </div>
  );
}
