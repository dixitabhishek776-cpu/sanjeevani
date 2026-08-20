"use client";

export default function CrisisBanner({ text }: { text: string }) {
  return (
    <div
      role="alert"
      style={{
        background: "var(--color-resource-bg)",
        border: "1px solid var(--color-resource)",
        borderRadius: "var(--radius)",
        padding: "var(--space-2)",
        marginBottom: "var(--space-2)",
        color: "var(--color-text)",
      }}
    >
      <strong style={{ color: "var(--color-resource)" }}>Support is available now.</strong>
      <p style={{ margin: "4px 0 0" }}>{text}</p>
    </div>
  );
}
