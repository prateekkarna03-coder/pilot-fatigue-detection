import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

interface MetricRowProps {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
}

function MetricRow({ label, value, unit, subtext }: MetricRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-[#f1f5f9] last:border-0">
      <div>
        <p className="text-sm text-[#475569]">{label}</p>
        {subtext && <p className="text-xs text-[#94a3b8]">{subtext}</p>}
      </div>
      <div className="text-right">
        <span className="text-base font-semibold tabular-nums text-[#1e2d4a]">
          {value}
        </span>
        {unit && <span className="ml-1 text-xs text-[#94a3b8]">{unit}</span>}
      </div>
    </div>
  );
}

interface SignalMetricsPanelProps {
  eyeClosurePercent: number;
  blinkRatePerMin: number;
  yawnCount: number;
  headPoseDeviation: number;
  alertsTriggered: number;
}

export function SignalMetricsPanel({
  eyeClosurePercent,
  blinkRatePerMin,
  yawnCount,
  headPoseDeviation,
  alertsTriggered,
}: SignalMetricsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Signal Metrics</CardTitle>
      </CardHeader>
      <CardContent className="px-5 pb-5 pt-0">
        <MetricRow
          label="Eye Closure Rate"
          value={eyeClosurePercent.toFixed(1)}
          unit="%"
          subtext="PERCLOS"
        />
        <MetricRow
          label="Blink Rate"
          value={blinkRatePerMin}
          unit="bpm"
          subtext="Normal: 15–20 bpm"
        />
        <MetricRow
          label="Yawn Count"
          value={yawnCount}
          unit="this hour"
        />
        <MetricRow
          label="Head Pose Deviation"
          value={headPoseDeviation.toFixed(1)}
          unit="°"
          subtext="Threshold: ±10°"
        />
        <MetricRow
          label="Alerts Triggered"
          value={alertsTriggered}
          unit="today"
        />
      </CardContent>
    </Card>
  );
}
