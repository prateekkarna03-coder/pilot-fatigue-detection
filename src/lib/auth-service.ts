/**
 * auth-service.ts
 *
 * The single source of truth for credential verification.
 * Both Auth.js authorize() and any API route reuse this function.
 *
 * Returns a discriminated union — never null, never throws to callers.
 * Status codes map directly to HTTP semantics.
 */

import { compare } from "bcryptjs";
import { prisma } from "@/lib/prisma";

// ── Types ──────────────────────────────────────────────────────────────────

export type AuthUser = {
  id: string;
  email: string;
  name: string;
  role: string;
};

export type AuthSuccess = {
  success: true;
  status: 200;
  user: AuthUser;
};

export type AuthFailure = {
  success: false;
  status: 400 | 401 | 429 | 500;
  error: string;
};

export type AuthResult = AuthSuccess | AuthFailure;

// ── Constants ──────────────────────────────────────────────────────────────

const MAX_EMAIL_LENGTH = 254; // RFC 5321
const MAX_PASSWORD_LENGTH = 128;
const MIN_PASSWORD_LENGTH = 1;

// A single generic message for all credential failures — never reveal
// whether the account exists.
const INVALID_CREDENTIALS_MSG = "Invalid email or password.";

// ── Rate Limiter ───────────────────────────────────────────────────────────
// In-memory token bucket. Capacity: 9 tokens. Refill: 9 tokens / minute.
// Consumes 1 token per failed login attempt.

type TokenBucketEntry = {
  tokens: number;
  lastRefill: number;
};

const CAPACITY = 9;
const REFILL_RATE_PER_MS = CAPACITY / (60 * 1000); // 0.15 tokens per second

const rateLimitMap = new Map<string, TokenBucketEntry>();

function getRateLimitKey(email: string, ip: string): string {
  // Key on both email AND IP to prevent distributed enumeration
  return `${ip}:${email.toLowerCase()}`;
}

function getVirtualTokens(entry: TokenBucketEntry, now: number): number {
  const elapsed = Math.max(0, now - entry.lastRefill);
  const newTokens = entry.tokens + elapsed * REFILL_RATE_PER_MS;
  return Math.min(CAPACITY, newTokens);
}

function isRateLimited(key: string): boolean {
  const entry = rateLimitMap.get(key);
  if (!entry) return false;
  return getVirtualTokens(entry, Date.now()) < 1;
}

function recordFailure(key: string): void {
  const now = Date.now();
  let tokens = CAPACITY;
  
  const entry = rateLimitMap.get(key);
  if (entry) {
    tokens = getVirtualTokens(entry, now);
  }
  
  rateLimitMap.set(key, {
    tokens: Math.max(0, tokens - 1),
    lastRefill: now,
  });

  // Basic cleanup to prevent memory leak (prune untouched entries after 10 mins)
  if (rateLimitMap.size > 10_000) {
    const threshold = now - 10 * 60 * 1000;
    for (const [k, v] of rateLimitMap.entries()) {
      if (v.lastRefill < threshold) rateLimitMap.delete(k);
    }
  }
}

function clearFailures(key: string): void {
  rateLimitMap.delete(key);
}

// ── Input validation ───────────────────────────────────────────────────────

type RawCredentials = {
  email?: unknown;
  password?: unknown;
};

function validateInput(raw: RawCredentials):
  | { valid: true; email: string; password: string }
  | { valid: false; error: string } {
  if (
    typeof raw.email !== "string" ||
    typeof raw.password !== "string" ||
    raw.email.trim() === "" ||
    raw.password === ""
  ) {
    return { valid: false, error: "Email and password are required." };
  }

  const email = raw.email.trim().toLowerCase();

  if (email.length > MAX_EMAIL_LENGTH) {
    return { valid: false, error: "Email address is too long." };
  }

  // Basic RFC-5322 structural check: must contain exactly one @
  if (!email.includes("@") || email.split("@").length !== 2) {
    return { valid: false, error: "Email address is not valid." };
  }

  if (
    raw.password.length < MIN_PASSWORD_LENGTH ||
    raw.password.length > MAX_PASSWORD_LENGTH
  ) {
    return { valid: false, error: "Password length is not valid." };
  }

  return { valid: true, email, password: raw.password };
}

// ── Main service function ──────────────────────────────────────────────────

/**
 * Verify credentials and return a typed AuthResult.
 *
 * @param rawCredentials  Untrusted input from a form/API.
 * @param clientIp        Caller's IP address for rate-limiting.
 */
export async function verifyCredentials(
  rawCredentials: RawCredentials,
  clientIp: string
): Promise<AuthResult> {
  // 1. Validate input shape
  const validation = validateInput(rawCredentials);
  if (!validation.valid) {
    return { success: false, status: 400, error: validation.error };
  }

  const { email, password } = validation;
  const rateLimitKey = getRateLimitKey(email, clientIp);

  // 2. Check rate limit before hitting the database
  if (isRateLimited(rateLimitKey)) {
    return {
      success: false,
      status: 429,
      error: "Too many failed attempts. Please wait a moment and try again.",
    };
  }

  // 3. Look up user — suppress all DB errors from the caller
  let user: {
    id: string;
    email: string;
    name: string;
    role: string;
    passwordHash: string;
  } | null;

  try {
    user = await prisma.user.findUnique({
      where: { email },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        passwordHash: true,
      },
    });
  } catch {
    // DB error — do not leak details
    return {
      success: false,
      status: 500,
      error: "An unexpected error occurred. Please try again later.",
    };
  }

  // 4. Always run bcrypt compare to prevent timing-based user enumeration.
  //    If the user doesn't exist we compare against a dummy hash so the
  //    response time is indistinguishable from a real failed comparison.
  const DUMMY_HASH =
    "$2b$12$x7yJOG7Xf7XXxxqYskSYyuuaLNhYtpvJ9SNi0KE1cLbvOEW914Xzi";

  const hashToCompare = user ? user.passwordHash : DUMMY_HASH;

  let passwordValid: boolean;
  try {
    passwordValid = await compare(password, hashToCompare);
  } catch {
    return {
      success: false,
      status: 500,
      error: "An unexpected error occurred. Please try again later.",
    };
  }

  // 5. Reject if no user or password mismatch — same message always
  if (!user || !passwordValid) {
    recordFailure(rateLimitKey);
    return { success: false, status: 401, error: INVALID_CREDENTIALS_MSG };
  }

  // 6. Success — clear failure counter, return safe fields only
  clearFailures(rateLimitKey);

  return {
    success: true,
    status: 200,
    user: {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      // passwordHash is intentionally excluded
    },
  };
}
