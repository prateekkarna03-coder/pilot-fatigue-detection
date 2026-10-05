/**
 * auth.ts
 *
 * Auth.js v4 configuration.
 * Credential verification is fully delegated to verifyCredentials() in
 * auth-service.ts — this file contains only Auth.js wiring.
 */

import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import { verifyCredentials } from "@/lib/auth-service";

// Auth.js authorize() runs server-side only; its return value flows into
// the JWT callback. It must return null to signal failure (Auth.js API
// contract) — real HTTP status codes are enforced at the API/login layer.

export const authOptions: NextAuthOptions = {
  session: {
    strategy: "jwt",
    maxAge: 8 * 60 * 60, // 8 hours — typical ops shift
  },

  pages: {
    signIn: "/login",
    error: "/login",
  },

  providers: [
    CredentialsProvider({
      id: "credentials",
      name: "Email & Password",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },

      async authorize(credentials, req) {
        // Extract caller IP for rate limiting.
        // In production behind a reverse proxy, set NEXTAUTH_URL and trust
        // the X-Forwarded-For header only from your proxy.
        const ip =
          (req.headers?.["x-forwarded-for"] as string)?.split(",")[0]?.trim() ??
          (req.headers?.["x-real-ip"] as string)?.trim() ??
          "unknown";

        const result = await verifyCredentials(
          { email: credentials?.email, password: credentials?.password },
          ip
        );

        if (!result.success) {
          // Auth.js requires null for any failure — the login page reads the
          // `error` query param and maps it to a user-friendly message.
          return null;
        }

        return result.user;
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.role = (user as unknown as { role: string }).role;
      }
      return token;
    },

    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
      }
      return session;
    },
  },

  // Cookie settings are intentionally left to Auth.js defaults:
  // - HttpOnly: true
  // - SameSite: lax
  // - Secure: true in production (when NEXTAUTH_URL starts with https://)
  // Override only if you have a specific deployment requirement.
};
