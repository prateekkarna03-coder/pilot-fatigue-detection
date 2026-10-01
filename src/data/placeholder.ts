import type {
  DashboardSummary,
  MonitoringSession,
  FatigueMetrics,
  TrendPoint,
  AiRecommendation,
  Report,
} from "@/types";

// ── Dashboard ──────────────────────────────────────────────────────────────

export const DASHBOARD_SUMMARY: DashboardSummary = {
  activeSessions: 8,
  highRiskPilots: 2,
  alertsToday: 14,
  avgFatigueScore: 34,
};

export const RECENT_SESSIONS: MonitoringSession[] = [
  {
    id: "SES-001",
    pilotId: "PLT-042",
    pilotName: "Capt. James Morrison",
    flightId: "AA-2847",
    date: "2026-10-01",
    duration: "6h 12m",
    avgFatigueScore: 62,
    peakRiskLevel: "High",
    alertsCount: 5,
    status: "Flagged",
  },
  {
    id: "SES-002",
    pilotId: "PLT-017",
    pilotName: "F/O Sarah Tran",
    flightId: "UA-1130",
    date: "2026-10-01",
    duration: "3h 45m",
    avgFatigueScore: 28,
    peakRiskLevel: "Low",
    alertsCount: 0,
    status: "Completed",
  },
  {
    id: "SES-003",
    pilotId: "PLT-089",
    pilotName: "Capt. Ricardo Vega",
    flightId: "DL-5501",
    date: "2026-10-01",
    duration: "8h 03m",
    avgFatigueScore: 74,
    peakRiskLevel: "Critical",
    alertsCount: 11,
    status: "Flagged",
  },
  {
    id: "SES-004",
    pilotId: "PLT-031",
    pilotName: "F/O Emily Walsh",
    flightId: "SW-8890",
    date: "2026-09-30",
    duration: "5h 20m",
    avgFatigueScore: 41,
    peakRiskLevel: "Moderate",
    alertsCount: 3,
    status: "Completed",
  },
  {
    id: "SES-005",
    pilotId: "PLT-055",
    pilotName: "Capt. David Kim",
    flightId: "BA-0392",
    date: "2026-09-30",
    duration: "9h 58m",
    avgFatigueScore: 19,
    peakRiskLevel: "Low",
    alertsCount: 0,
    status: "Completed",
  },
];

// ── Live Monitoring ────────────────────────────────────────────────────────

export const LIVE_METRICS: FatigueMetrics = {
  fatigueScore: 67,
  riskLevel: "High",
  eyeClosurePercent: 4.8,
  blinkRatePerMin: 11,
  yawnCount: 7,
  headPoseDeviation: 14.2,
  alertsTriggered: 4,
};

export const TREND_DATA: TrendPoint[] = [
  { time: "08:00", score: 18 },
  { time: "09:00", score: 22 },
  { time: "10:00", score: 31 },
  { time: "11:00", score: 45 },
  { time: "12:00", score: 52 },
  { time: "13:00", score: 67 },
  { time: "14:00", score: 60 },
  { time: "15:00", score: 71 },
];

export const AI_RECOMMENDATIONS: AiRecommendation[] = [
  {
    id: "REC-001",
    severity: "High",
    message:
      "Pilot eye-closure rate has exceeded the 4% threshold for the past 30 minutes. Consider cockpit crew rest rotation.",
    issuedAt: "14:05",
  },
  {
    id: "REC-002",
    severity: "Moderate",
    message:
      "Blink rate has dropped below 12 bpm. Recommend activating in-seat alert protocol.",
    issuedAt: "13:48",
  },
  {
    id: "REC-003",
    severity: "High",
    message:
      "Head pose deviation >10° detected 3 times in the last hour — consistent with microsleep episodes.",
    issuedAt: "13:21",
  },
];

// ── History ────────────────────────────────────────────────────────────────

export const ALL_SESSIONS: MonitoringSession[] = [
  ...RECENT_SESSIONS,
  {
    id: "SES-006",
    pilotId: "PLT-072",
    pilotName: "Capt. Linda Park",
    flightId: "QF-0012",
    date: "2026-09-29",
    duration: "11h 40m",
    avgFatigueScore: 55,
    peakRiskLevel: "Moderate",
    alertsCount: 6,
    status: "Completed",
  },
  {
    id: "SES-007",
    pilotId: "PLT-019",
    pilotName: "F/O Connor O'Brien",
    flightId: "EK-2201",
    date: "2026-09-29",
    duration: "7h 15m",
    avgFatigueScore: 38,
    peakRiskLevel: "Low",
    alertsCount: 1,
    status: "Completed",
  },
  {
    id: "SES-008",
    pilotId: "PLT-088",
    pilotName: "Capt. Nadia Petrov",
    flightId: "SU-2650",
    date: "2026-09-28",
    duration: "4h 50m",
    avgFatigueScore: 82,
    peakRiskLevel: "Critical",
    alertsCount: 15,
    status: "Flagged",
  },
];

// ── Reports ────────────────────────────────────────────────────────────────

export const REPORTS: Report[] = [
  {
    id: "RPT-001",
    reportType: "Session Summary",
    relatedPilot: "Capt. James Morrison",
    period: "Oct 1, 2026",
    generatedDate: "2026-10-01",
    status: "Generated",
    fileSizeKb: 312,
  },
  {
    id: "RPT-002",
    reportType: "Incident Report",
    relatedPilot: "Capt. Ricardo Vega",
    period: "Oct 1, 2026",
    generatedDate: "2026-10-01",
    status: "Generated",
    fileSizeKb: 540,
  },
  {
    id: "RPT-003",
    reportType: "Weekly Overview",
    relatedPilot: "All Pilots",
    period: "Sep 25 – Oct 1, 2026",
    generatedDate: "2026-10-01",
    status: "Pending",
    fileSizeKb: 0,
  },
  {
    id: "RPT-004",
    reportType: "Session Summary",
    relatedPilot: "Capt. Nadia Petrov",
    period: "Sep 28, 2026",
    generatedDate: "2026-09-28",
    status: "Generated",
    fileSizeKb: 287,
  },
  {
    id: "RPT-005",
    reportType: "Incident Report",
    relatedPilot: "F/O Sarah Tran",
    period: "Sep 30, 2026",
    generatedDate: "2026-09-30",
    status: "Failed",
    fileSizeKb: 0,
  },
];
