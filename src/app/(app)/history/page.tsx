import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { RecentSessionsTable } from "@/components/dashboard/recent-sessions-table";
import type { MonitoringSession, RiskLevel, SessionStatus } from "@/types";

export const metadata: Metadata = { title: "Session History" };

const RISK_LEVELS: RiskLevel[] = ["Low", "Moderate", "High", "Critical"];

function formatDuration(startedAt: Date, endedAt: Date | null) {
  const durationMs = Math.max(0, (endedAt ?? new Date()).getTime() - startedAt.getTime());
  const totalMinutes = Math.floor(durationMs / 60_000);
  return `${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m`;
}

function mapSessionStatus(status: string): SessionStatus {
  switch (status) {
    case "ACTIVE":
      return "Active";
    case "COMPLETED":
      return "Completed";
    case "ABORTED":
      return "Aborted";
    case "FLAGGED":
      return "Flagged";
    default:
      return "Aborted";
  }
}

function mapRiskLevel(level: string): RiskLevel {
  return level.charAt(0) + level.slice(1).toLowerCase() as RiskLevel;
}

export default async function HistoryPage() {
  const authSession = await getServerSession(authOptions);

  if (!authSession?.user?.email) {
    redirect("/login");
  }

  const pilot = await prisma.pilot.findUnique({
    where: { email: authSession.user.email },
  });

  if (!pilot) {
    redirect("/dashboard");
  }

  const databaseSessions = await prisma.monitoringSession.findMany({
    where: { pilotId: pilot.id },
    orderBy: { startedAt: "desc" },
    take: 100,
    include: {
      flight: { select: { flightCode: true } },
      measurements: { select: { fatigueScore: true } },
      riskHistory: {
        select: { riskLevel: true },
        orderBy: { triggeredAt: "desc" },
      },
    },
  });

  const sessions: MonitoringSession[] = databaseSessions.map((session) => {
    const scores = session.measurements.map((measurement) => measurement.fatigueScore);
    const averageScore = scores.length
      ? scores.reduce((sum, score) => sum + score, 0) / scores.length
      : 0;
    const peakRisk = session.riskHistory.reduce<RiskLevel>((peak, risk) => {
      const current = mapRiskLevel(risk.riskLevel);
      return RISK_LEVELS.indexOf(current) > RISK_LEVELS.indexOf(peak) ? current : peak;
    }, "Low");

    return {
      id: session.id,
      pilotId: session.pilotId,
      pilotName: pilot.name,
      flightId: session.flight.flightCode,
      date: session.startedAt.toISOString().slice(0, 10),
      duration: formatDuration(session.startedAt, session.endedAt),
      avgFatigueScore: Math.round(averageScore * 10) / 10,
      peakRiskLevel: peakRisk,
      alertsCount: session.alertCount,
      status: mapSessionStatus(session.status),
    };
  });

  return (
    <>
      <TopBar
        title="Session History"
        subtitle="Complete log of all pilot monitoring sessions"
        actions={
          <Button variant="outline" size="sm">
            Export CSV
          </Button>
        }
      />

      <main className="flex-1 overflow-y-auto p-6">
        <div className="rounded-lg border border-[#e2e8f0] bg-white shadow-sm">
          {/* Table header bar */}
          <div className="flex items-center justify-between border-b border-[#e2e8f0] px-5 py-3.5">
            <h2 className="text-sm font-semibold text-[#1e2d4a]">
              All Sessions
              <span className="ml-2 text-xs font-normal text-[#94a3b8]">
                ({sessions.length} records)
              </span>
            </h2>
          </div>

          <RecentSessionsTable sessions={sessions} />
        </div>
      </main>
    </>
  );
}
