import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import { TopBar } from "@/components/layout/top-bar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TrendChart } from "@/components/monitoring/trend-chart";
import { AiRecommendationsPanel } from "@/components/monitoring/ai-recommendations-panel";
import { StopMonitoringButton } from "@/components/monitoring/stop-monitoring-button";
import { LiveMonitoringProvider, FatigueScoreClientPanel, SignalMetricsClientPanel } from "@/components/monitoring/live-monitoring-provider";
import { getGeminiStatus } from "@/lib/gemini";
import { classifyRisk } from "@/lib/risk-level";
export const dynamic = "force-dynamic";
export const revalidate = 0;
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

  // Fetch exactly ONE active session, ensuring the latest active session is selected
  const activeSession = await prisma.monitoringSession.findFirst({
    where: {
      pilotId: pilot.id,
      status: "ACTIVE",
    },
    orderBy: {
      startedAt: "desc",
    },
    include: {
      flight: true,
      measurements: {
        orderBy: { capturedAt: "desc" },
        take: 50
      },
      recommendations: {
        orderBy: { issuedAt: "desc" },
        take: 3
      },
      riskHistory: {
        orderBy: { triggeredAt: "desc" },
        take: 1
      }
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


  // Generate formatted historical telemetry queue for chart rendering
  const mappedTrend = activeSession.measurements.map(m => ({
    time: m.capturedAt.toISOString().slice(11, 19),
    score: m.fatigueScore,
    timestamp: m.capturedAt.toISOString(),
  })).reverse();

  const mappedRecommendations = activeSession.recommendations.map(r => ({
    id: r.id,
    severity: r.severity,
    message: r.message,
    issuedAt: r.issuedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }));

  const latestMeasurement = activeSession.measurements[0];
  const initialMetrics = latestMeasurement ? {
    fatigueScore: latestMeasurement.fatigueScore,
    modelKss: null,
    riskLevel: (classifyRisk(latestMeasurement.fatigueScore, 0).charAt(0) + classifyRisk(latestMeasurement.fatigueScore, 0).slice(1).toLowerCase()) as "Low" | "Moderate" | "High" | "Critical",
    eyeClosurePercent: latestMeasurement.eyeClosurePercent,
    blinkRatePerMin: latestMeasurement.blinkRatePerMin,
    yawnCount: latestMeasurement.yawnCount,
    headPoseDeviation: Math.round(Math.abs(latestMeasurement.headPosePitch) + Math.abs(latestMeasurement.headPoseYaw)),
    alertsTriggered: activeSession.alertCount,
    trendData: mappedTrend,
  } : {
    trendData: mappedTrend,
  };

  return (
    <LiveMonitoringProvider sessionId={activeSession.id} initialData={initialMetrics}>
      <TopBar
        title="Live Monitoring"
        subtitle={`${pilot.name} · Flight ${activeSession.flight.flightCode} · Elapsed: ${elapsedFormatted}`}
        actions={
          <StopMonitoringButton sessionId={activeSession.id} />
        }
      />

      <main className="flex-1 min-h-0 overflow-y-auto p-4 lg:overflow-hidden">
        <div className="grid min-h-full gap-3 lg:grid-rows-[minmax(0,1fr)_10.5rem]">
          <section className="grid min-h-0 gap-3 lg:grid-cols-2">
            <FatigueScoreClientPanel />
            <div className="grid min-h-0 gap-3 sm:grid-cols-2">
              <Card className="min-h-0">
                <CardHeader className="p-4 pb-2">
                  <CardTitle>Session Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-1 px-4 pb-3 pt-0 text-xs">
                  {[
                    ["Pilot", pilot.name],
                    ["Flight ID", activeSession.flight.flightCode],
                    ["Session Start", startLocalFormatted],
                    ["Elapsed", elapsedFormatted],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="flex justify-between gap-2 border-b border-[#f1f5f9] py-1 last:border-0"
                    >
                      <span className="text-[#94a3b8]">{label}</span>
                      <span className="truncate font-medium text-[#1e2d4a]">{value}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <SignalMetricsClientPanel />
            </div>
          </section>

          <section className="grid min-h-0 gap-3 lg:grid-cols-2">
            <TrendChart />
            <AiRecommendationsPanel
              recommendations={mappedRecommendations}
              status={getGeminiStatus()}
              sessionId={activeSession.id}
            />
          </section>
        </div>
      </main>
    </LiveMonitoringProvider>
  );
}
