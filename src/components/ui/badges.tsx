import { cn } from "@/lib/utils";
import type { RiskLevel, SessionStatus, ReportStatus } from "@/types";

// ── Risk Level Badge ───────────────────────────────────────────────────────

export const RISK_STYLES: Record<string, string> = {
  Low: "bg-green-50 text-green-700 border-green-200",
  LOW: "bg-green-50 text-green-700 border-green-200",
  Moderate: "bg-amber-50 text-amber-700 border-amber-200",
  MODERATE: "bg-amber-50 text-amber-700 border-amber-200",
  High: "bg-orange-50 text-orange-700 border-orange-200",
  HIGH: "bg-orange-50 text-orange-700 border-orange-200",
  Critical: "bg-red-50 text-red-700 border-red-200",
  CRITICAL: "bg-red-50 text-red-700 border-red-200",
};

export function getRiskBadgeStyle(level: string): string {
  if (RISK_STYLES[level]) return RISK_STYLES[level];
  const normalizedKey = level
    ? level.charAt(0).toUpperCase() + level.slice(1).toLowerCase()
    : "Low";
  return RISK_STYLES[normalizedKey] ?? RISK_STYLES.Low;
}

interface RiskBadgeProps {
  level: RiskLevel | "LOW" | "MODERATE" | "HIGH" | "CRITICAL" | string;
  className?: string;
}

export function RiskBadge({ level, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium",
        getRiskBadgeStyle(level),
        className
      )}
    >
      {level}
    </span>
  );
}

// ── Session Status Badge ───────────────────────────────────────────────────

const SESSION_STATUS_STYLES: Record<SessionStatus, string> = {
  Active: "bg-blue-50 text-blue-700 border-blue-200",
  Completed: "bg-slate-100 text-slate-600 border-slate-200",
  Flagged: "bg-red-50 text-red-700 border-red-200",
  Aborted: "bg-red-50 text-red-700 border-red-200",
};

interface SessionStatusBadgeProps {
  status: SessionStatus;
  className?: string;
}

export function SessionStatusBadge({ status, className }: SessionStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium",
        SESSION_STATUS_STYLES[status],
        className
      )}
    >
      {status}
    </span>
  );
}

// ── Report Status Badge ────────────────────────────────────────────────────

const REPORT_STATUS_STYLES: Record<ReportStatus, string> = {
  Generated: "bg-green-50 text-green-700 border-green-200",
  Pending: "bg-amber-50 text-amber-700 border-amber-200",
  Failed: "bg-red-50 text-red-700 border-red-200",
};

interface ReportStatusBadgeProps {
  status: ReportStatus;
  className?: string;
}

export function ReportStatusBadge({ status, className }: ReportStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-medium",
        REPORT_STATUS_STYLES[status],
        className
      )}
    >
      {status}
    </span>
  );
}
