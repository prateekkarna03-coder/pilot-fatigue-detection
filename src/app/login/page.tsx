import type { Metadata } from "next";
import { ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const metadata: Metadata = {
  title: "Sign In",
};

export default function LoginPage() {
  return (
    <div className="flex h-full min-h-screen items-center justify-center bg-[#f4f6f9] px-4">
      <div className="w-full max-w-sm">
        {/* Brand */}
        <div className="mb-8 flex flex-col items-center gap-2 text-center">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-[#e2e8f0] bg-white shadow-sm">
            <ShieldCheck className="h-6 w-6 text-[#1e2d4a]" />
          </div>
          <h1 className="text-xl font-bold text-[#1e2d4a]">
            Pilot Safety Monitor
          </h1>
          <p className="text-sm text-[#94a3b8]">
            Sign in to your operations account
          </p>
        </div>

        {/* Form card */}
        <div className="rounded-lg border border-[#e2e8f0] bg-white p-6 shadow-sm">
          <form className="flex flex-col gap-4" action="/dashboard">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                placeholder="ops@aviation.sys"
                autoComplete="email"
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <button
                  type="button"
                  className="text-xs text-[#1e2d4a] hover:underline focus:outline-none"
                >
                  Forgot password?
                </button>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                required
              />
            </div>

            <Button type="submit" className="mt-1 w-full">
              Sign In
            </Button>
          </form>
        </div>

        <p className="mt-5 text-center text-xs text-[#94a3b8]">
          Restricted system — authorised personnel only.
        </p>
      </div>
    </div>
  );
}
