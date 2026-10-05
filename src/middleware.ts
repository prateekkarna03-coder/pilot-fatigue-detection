import { withAuth } from "next-auth/middleware";
import { NextResponse } from "next/server";

export default withAuth(
  function middleware() {
    // If the user has a valid token, allow the request through.
    return NextResponse.next();
  },
  {
    callbacks: {
      // Return true when the user is authenticated (token exists).
      authorized({ token }) {
        return !!token;
      },
    },
  }
);

// Protect all routes except /login and static/API paths
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     *   - /login (public)
     *   - /api/auth/* (Auth.js endpoints)
     *   - /_next/* (Next.js internals)
     *   - /favicon.ico, /public assets
     */
    "/((?!login|api/auth|_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
