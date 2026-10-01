import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Pilot Safety & Fatigue Monitor",
    template: "%s | Pilot Safety",
  },
  description:
    "AI-powered human-aware pilot fatigue monitoring system for real-time safety analysis.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="h-full antialiased">{children}</body>
    </html>
  );
}
