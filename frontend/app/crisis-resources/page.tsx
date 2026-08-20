// Deliberately static content, no API dependency — per Ch.4 Sec.5,
// this must remain available even during a full backend outage.
export default function CrisisResourcesPage() {
  return (
    <div style={{ maxWidth: 560, margin: "0 auto", padding: "var(--space-3)" }}>
      <h1 style={{ fontSize: 22 }}>Support is available now</h1>
      <p>If you're in immediate danger, contact your local emergency number right away.</p>
      <ul>
        <li><strong>US:</strong> Call or text 988 (Suicide & Crisis Lifeline), 24/7</li>
        <li><strong>US:</strong> Text HOME to 741741 (Crisis Text Line)</li>
        <li><strong>International:</strong> findahelpline.com lists local crisis lines by country</li>
      </ul>
      <p>You don't have to be in crisis to reach out — these lines are there for whatever you're carrying.</p>
      <a href="/">Back to Sanjeevani</a>
    </div>
  );
}
