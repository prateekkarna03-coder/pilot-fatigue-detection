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
      authorized({ req, token }) {
        if (req.nextUrl.pathname.startsWith('/api/auth')) return true;
        if (req.nextUrl.pathname.startsWith('/login')) return true;
        if (
          req.nextUrl.pathname === '/api/telemetry' &&
          req.headers.get('x-telemetry-token') === process.env.NEXTAUTH_SECRET
        ) {
          return true;
        }
        
        return !!token;
      },
    },
  }
);

// Protect all routes except /login and static/API paths
export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon\\.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
