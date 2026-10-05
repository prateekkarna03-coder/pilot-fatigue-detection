import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { FatigueScorePanel } from "@/components/monitoring/fatigue-score-panel";
import { SignalMetricsPanel } from "@/components/monitoring/signal-metrics-panel";
import { TrendChart } from "@/components/monitoring/trend-chart";
import { AiRecommendationsPanel } from "@/components/monitoring/ai-recommendations-panel";
import { StopMonitoringButton } from "@/components/monitoring/stop-monitoring-button";
import { LIVE_METRICS, TREND_DATA, AI_RECOMMENDATIONS } from "@/data/placeholder";

export const metadata: Metadata = { title: "Live Monitoring" };

export default async function MonitoringPage() {
  const session = await getServerSession(authOptions);

  if (!session?.user?.email) {
    redirect("/login");
  }

  const pilot = await prisma.pilot.findUnique({
    where: { email: session.user.email },
  });

  if (!pilot) {
    redirect("/dashboard");
  }

  // Fetch exactly ONE active session
  const activeSession = await prisma.monitoringSession.findFirst({
    where: {
      pilotId: pilot.id,
      status: "ACTIVE",
    },
    include: {
      flight: true,
    },
  });

  if (!activeSession) {
    redirect("/dashboard"); // Safe fallback if no sessions are natively active
  }

  // Calculate elapsed time (mock styling formatting applied real-time)
  // eslint-disable-next-line
  const elapsedMs = Date.now() - activeSession.startedAt.getTime();
  const elapsedHours = Math.floor(elapsedMs / (1000 * 60 * 60));
  const elapsedMinutes = Math.floor((elapsedMs % (1000 * 60 * 60)) / (1000 * 60));
  const elapsedFormatted = `${elapsedHours}h ${elapsedMinutes}m`;
  
  // Format start time using UTC roughly
  const startLocalFormatted = activeSession.startedAt.toISOString().slice(11, 16) + " UTC";

  const {
    fatigueScore,
    riskLevel,
    eyeClosurePercent,
    blinkRatePerMin,
    yawnCount,
    headPoseDeviation,
    alertsTriggered,
  } = LIVE_METRICS;

  return (
    <>
      <TopBar
        title="Live Monitoring"
        subtitle={`${pilot.name} · Flight ${activeSession.flight.flightCode} · Elapsed: ${elapsedFormatted}`}
        actions={
          <StopMonitoringButton sessionId={activeSession.id} />
        }
      />

      <main className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Top row: score + session info + signal metrics */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {/* Fatigue score gauge */}
          <Card className="flex flex-col items-center justify-center py-6">
            <FatigueScorePanel score={fatigueScore} riskLevel={riskLevel} />
          </Card>

          {/* Session info */}
          <Card>
            <CardHeader>
              <CardTitle>Session Details</CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2 pt-0">
              {[
                ["Pilot", pilot.name],
                ["Flight ID", activeSession.flight.flightCode],
                ["Session Start", startLocalFormatted],
                ["Elapsed", elapsedFormatted],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex justify-between border-b border-[#f1f5f9] py-1.5 last:border-0"
                >
                  <span className="text-[#94a3b8]">{label}</span>
                  <span className="font-medium text-[#1e2d4a]">{value}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Signal metrics */}
          <SignalMetricsPanel
            eyeClosurePercent={eyeClosurePercent}
            blinkRatePerMin={blinkRatePerMin}
            yawnCount={yawnCount}
            headPoseDeviation={headPoseDeviation}
            alertsTriggered={alertsTriggered}
          />
        </div>

        {/* Bottom row: trend chart + AI recommendations */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <TrendChart data={TREND_DATA} />
          <AiRecommendationsPanel recommendations={AI_RECOMMENDATIONS} />
        </div>
      </main>
    </>
  );
}
