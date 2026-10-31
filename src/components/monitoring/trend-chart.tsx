'use client';

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useLiveMetrics } from "./live-monitoring-provider";

export function TrendChart() {
  const { trendData } = useLiveMetrics();
  const data = trendData;
  const max = 100;
  const chartHeight = 100;
  const chartWidth = 400;
  const padX = 8;
  const padY = 8;
  const innerW = chartWidth - padX * 2;
  const innerH = chartHeight - padY * 2;

  const points = data.map((d, i) => {
    const x = padX + (i / Math.max(1, data.length - 1)) * innerW;
    const y = padY + innerH - (d.score / max) * innerH;
    return { x, y, ...d };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(" ");
  const areaPath =
    points.length > 0
      ? `M ${points[0].x},${padY + innerH} ` +
        points.map((p) => `L ${p.x},${p.y}`).join(" ") +
        ` L ${points[points.length - 1].x},${padY + innerH} Z`
      : "";

  return (
    <Card>
      <CardHeader className="p-4 pb-2">
        <CardTitle>Fatigue Score Trend</CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-3">
        <div className="relative w-full">
          <svg
            viewBox={`0 0 ${chartWidth} ${chartHeight}`}
            className="w-full"
            aria-label="Fatigue score trend over time"
            role="img"
          >
            {/* Horizontal grid lines */}
            {[0, 25, 50, 75, 100].map((val) => {
              const y = padY + innerH - (val / max) * innerH;
              return (
                <g key={val}>
                  <line
                    x1={padX}
                    y1={y}
                    x2={padX + innerW}
                    y2={y}
                    stroke="#f1f5f9"
                    strokeWidth="1"
                  />
                  <text
                    x={padX - 2}
                    y={y + 3}
                    textAnchor="end"
                    style={{ fontSize: 7, fill: "#94a3b8" }}
                  >
                    {val}
                  </text>
                </g>
              );
            })}

            {data.length > 0 && (
              <>
                {/* Area fill */}
                <path d={areaPath} fill="#1e2d4a" fillOpacity="0.06" />

                {/* Line */}
                <polyline
                  points={polylinePoints}
                  fill="none"
                  stroke="#1e2d4a"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                  strokeLinecap="round"
                />

                {/* Data points */}
                {points.map((p, index) => (
                  <circle
                    key={`${p.timestamp ?? p.time}-${p.sequence ?? index}`}
                    cx={p.x}
                    cy={p.y}
                    r="2.5"
                    fill="#1e2d4a"
                    stroke="white"
                    strokeWidth="1"
                  />
                ))}

                {/* X-axis labels */}
                {points.map((p, index) => (
                  <text
                    key={`${p.timestamp ?? p.time}-${p.sequence ?? index}-label`}
                    x={p.x}
                    y={chartHeight - 1}
                    textAnchor="middle"
                    style={{ fontSize: 7, fill: "#94a3b8" }}
                  >
                    {p.time}
                  </text>
                ))}
              </>
            )}
          </svg>
          {data.length === 0 && (
            <p className="py-8 text-center text-sm text-[#94a3b8]">
              Waiting for live measurements...
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
