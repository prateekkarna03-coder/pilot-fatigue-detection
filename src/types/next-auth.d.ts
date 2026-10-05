import "next-auth";
import "next-auth/jwt";

// Augment Auth.js types to include custom fields on session.user and JWT token.
// This keeps TypeScript strict without casting.

declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      role: string;
      name?: string | null;
      email?: string | null;
      image?: string | null;
    };
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string;
    role: string;
  }
}
