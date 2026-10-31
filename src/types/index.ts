// ── Enums ──────────────────────────────────────────────────────────────────

export type RiskLevel = "Low" | "Moderate" | "High" | "Critical";
export type SessionStatus = "Active" | "Completed" | "Flagged" | "Aborted";
export type ReportStatus = "Generated" | "Pending" | "Failed";
export type ReportType = "Session Summary" | "Weekly Overview" | "Incident Report";

// ── Monitoring ─────────────────────────────────────────────────────────────

export interface FatigueMetrics {
  fatigueScore: number; // 0–100
  riskLevel: RiskLevel;
  eyeClosurePercent: number;
  blinkRatePerMin: number;
  yawnCount: number;
  headPoseDeviation: number; // degrees
  alertsTriggered: number;
}

export interface TrendPoint {
  time: string;
  score: number;
  timestamp?: string;
  sequence?: number;
}

export interface AiRecommendation {
  id: string;
  severity: RiskLevel | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  message: string;
  issuedAt: string;
}

// ── Session / History ──────────────────────────────────────────────────────

export interface MonitoringSession {
  id: string;
  pilotId: string;
  pilotName: string;
  flightId: string;
  date: string;         // ISO 8601 date string
  duration: string;     // e.g. "4h 32m"
  avgFatigueScore: number;
  peakRiskLevel: RiskLevel;
  alertsCount: number;
  status: SessionStatus;
}

// ── Reports ────────────────────────────────────────────────────────────────

export interface Report {
  id: string;
  reportType: ReportType;
  relatedPilot: string;
  period: string;
  generatedDate: string;
  status: ReportStatus;
  fileSizeKb: number;
}

// ── Dashboard ──────────────────────────────────────────────────────────────

export interface DashboardSummary {
  activeSessions: number;
  highRiskPilots: number;
  alertsToday: number;
  avgFatigueScore: number;
}
