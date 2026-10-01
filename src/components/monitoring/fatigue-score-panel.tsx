import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/types";

interface FatigueScoreGaugeProps {
  score: number;
  riskLevel: RiskLevel;
}

const RISK_COLOR: Record<RiskLevel, string> = {
  Low: "#16a34a",
  Moderate: "#d97706",
  High: "#ea580c",
  Critical: "#dc2626",
};

const RISK_BG: Record<RiskLevel, string> = {
  Low: "bg-green-50 border-green-200",
  Moderate: "bg-amber-50 border-amber-200",
  High: "bg-orange-50 border-orange-200",
  Critical: "bg-red-50 border-red-200",
};

const RISK_TEXT: Record<RiskLevel, string> = {
  Low: "text-green-700",
  Moderate: "text-amber-700",
  High: "text-orange-700",
  Critical: "text-red-700",
};

export function FatigueScorePanel({
  score,
  riskLevel,
}: FatigueScoreGaugeProps) {
  const color = RISK_COLOR[riskLevel];

  // SVG arc progress (simple semicircle gauge)
  const radius = 60;
  const cx = 80;
  const cy = 80;
  const circumference = Math.PI * radius; // half circle arc
  const progress = (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-3">
      <svg
        viewBox="0 0 160 100"
        className="w-48"
        aria-label={`Fatigue score: ${score}`}
        role="img"
      >
        {/* Background arc */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth="12"
          strokeLinecap="round"
        />
        {/* Progress arc */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
        />
        {/* Score text */}
        <text
          x={cx}
          y={cy - 6}
          textAnchor="middle"
          className="font-bold"
          style={{ fontSize: 26, fill: "#1e2d4a", fontWeight: 700 }}
        >
          {score}
        </text>
        <text
          x={cx}
          y={cy + 10}
          textAnchor="middle"
          style={{ fontSize: 10, fill: "#94a3b8" }}
        >
          / 100
        </text>
      </svg>

      <div className={cn("rounded border px-3 py-1 text-sm font-semibold", RISK_BG[riskLevel], RISK_TEXT[riskLevel])}>
        {riskLevel} Risk
      </div>
      <p className="text-xs text-[#94a3b8]">Current Fatigue Score</p>
    </div>
  );
}
