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
  connectionStatus: string;
}

export function SignalMetricsPanel({
  eyeClosurePercent,
  blinkRatePerMin,
  yawnCount,
  headPoseDeviation,
  alertsTriggered,
  connectionStatus,
}: SignalMetricsPanelProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between p-4 pb-2">
        <CardTitle>Signal Metrics</CardTitle>
        <div className={`text-xs px-2 py-1 rounded border font-semibold ${
          connectionStatus === 'Connected' ? 'bg-green-50 text-green-700 border-green-200' : 
          connectionStatus === 'Connecting' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-red-50 text-red-700 border-red-200'
        }`}>
          {connectionStatus}
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-3 pt-0">
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
