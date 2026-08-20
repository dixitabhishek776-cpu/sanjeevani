import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Sanjeevani",
  description: "A calm, private space to reflect.",
  manifest: "/manifest.webmanifest",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div
          style={{
            position: "sticky",
            top: 0,
            zIndex: 9999,
            width: "100%",
            background: "#b91c1c",
            color: "#fff",
            textAlign: "center",
            padding: "10px 16px",
            fontSize: "14px",
            fontWeight: 600,
            lineHeight: 1.4,
          }}
        >
          ⚠️ PORTFOLIO DEMO — This is a student engineering project, not a real
          crisis-support service. It has not been clinically or legally
          reviewed. If you are in crisis, please contact a real local
          emergency service or crisis line instead.
        </div>
        {children}
      </body>
    </html>
  );
}
