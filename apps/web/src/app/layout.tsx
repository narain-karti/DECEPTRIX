import type { Metadata } from "next";
import "../styles/globals.css";
import AppShell from "../components/shared/AppShell";

export const metadata: Metadata = {
  title: "DECEPTRIX — Evidence Before Conclusions",
  description:
    "Evidence-first trust infrastructure for investigating suspicious media and social-media rumours. Media Audit for videos, Rumour Audit for claims.",
  keywords: "deepfake detection, misinformation, fact-check, evidence, provenance, media audit, rumour audit",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
