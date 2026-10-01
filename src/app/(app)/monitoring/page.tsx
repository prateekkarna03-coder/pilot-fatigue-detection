import type { Metadata } from "next";
import { TopBar } from "@/components/layout/top-bar";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { FatigueScorePanel } from "@/components/monitoring/fatigue-score-panel";
import { SignalMetricsPanel } from "@/components/monitoring/signal-metrics-panel";
import { TrendChart } from "@/components/monitoring/trend-chart";
import { AiRecommendationsPanel } from "@/components/monitoring/ai-recommendations-panel";
import { LIVE_METRICS, TREND_DATA, AI_RECOMMENDATIONS } from "@/data/placeholder";

export const metadata: Metadata = { title: "Live Monitoring" };

// Pilot context for the demo — will come from session/context in production
const MONITORED_PILOT = {
  name: "Capt. James Morrison",
  flightId: "AA-2847",
  startTime: "08:00 UTC",
  elapsed: "6h 12m",
};

export default function MonitoringPage() {
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
        subtitle={`${MONITORED_PILOT.name} · Flight ${MONITORED_PILOT.flightId} · Elapsed: ${MONITORED_PILOT.elapsed}`}
        actions={
          <Button variant="outline" size="sm">
            End Session
          </Button>
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
                ["Pilot", MONITORED_PILOT.name],
                ["Flight ID", MONITORED_PILOT.flightId],
                ["Session Start", MONITORED_PILOT.startTime],
                ["Elapsed", MONITORED_PILOT.elapsed],
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
