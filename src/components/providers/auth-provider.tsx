"use client";

import { SessionProvider } from "next-auth/react";

// Thin wrapper so we can use "use client" here while keeping layout.tsx
// as a Server Component.
export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
